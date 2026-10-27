import os
import sys
import json
import uuid
import queue
import asyncio
import threading
from contextlib import asynccontextmanager
import pika
import requests
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from seguranca import assinar_payload, validar_envelope

RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "rabbitmq")
MS_ESTOQUE_URL = os.getenv("MS_ESTOQUE_URL", "http://localhost:8001")

ORIGEM_CHAVES = {
    "pedido.estoque_ok": "public_keys/estoque.pem",
    "estoque.indisponivel": "public_keys/estoque.pem",
    "pagamento.pendente": "public_keys/pagamento.pem",
    "pagamento.aprovado": "public_keys/pagamento.pem",
    "pagamento.recusado": "public_keys/pagamento.pem",
    "pedido.enviado": "public_keys/entrega.pem",
}

MAPA_STATUS_AMIGAVEL = {
    "pedido.criado": "Pedido Criado (Aguardando Estoque)",
    "pedido.estoque_ok": "Estoque Confirmado",
    "estoque.indisponivel": "Estoque Indisponível",
    "pagamento.pendente": "Pagamento Pendente (Aguardando Checkout)",
    "pagamento.aprovado": "Pagamento Aprovado",
    "pagamento.recusado": "Pagamento Recusado",
    "pedido.enviado": "Pedido Enviado",
    "pedido.excluido": "Pedido Excluído",
}

pedidos = {}
clientes_sse: list[queue.Queue] = []


class CriarPedidoRequest(BaseModel):
    produtos: dict[str, int]


class InteressePromocaoRequest(BaseModel):
    email: str
    categorias: list[str] = ["A", "B", "C"]


def notificar_clientes_sse(evento_dados: dict):
    """Envia uma notificação em tempo real para todas as conexões SSE ativas."""
    for fila_cliente in list(clientes_sse):
        fila_cliente.put(evento_dados)


def publish(routing_key: str, mensagem: dict):
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host=RABBITMQ_HOST)
    )
    channel = connection.channel()

    channel.exchange_declare(exchange="eCommerce", exchange_type="direct")
    payload = assinar_payload(mensagem, key_path="private_key.pem")

    channel.basic_publish(
        exchange="eCommerce",
        routing_key=routing_key,
        body=json.dumps(payload),
    )
    connection.close()


def callback_consumidor(ch, method, properties, body):
    evento = method.routing_key
    key = ORIGEM_CHAVES.get(evento)
    mensagem = validar_envelope(body.decode("utf-8"), key_path=key)

    if mensagem is None:
        print(f"\n [❌] Descartado {evento}: Assinatura digital inválida!")
        ch.basic_ack(delivery_tag=method.delivery_tag)
        return

    id_pedido = mensagem.get("id_pedido")

    if id_pedido in pedidos:
        status_legivel = MAPA_STATUS_AMIGAVEL.get(evento, evento)
        pedidos[id_pedido]["status"] = evento
        pedidos[id_pedido]["status_descricao"] = status_legivel

        if "valor_total" in mensagem:
            pedidos[id_pedido]["valor_total"] = mensagem["valor_total"]

        if "checkout_url" in mensagem:
            pedidos[id_pedido]["checkout_url"] = mensagem["checkout_url"]

        print(f"Pedido {id_pedido} atualizado para: {evento} ({status_legivel})")

        # Emite notificação SSE em tempo real para o Frontend sobre a mudança de estado
        notificar_clientes_sse({
            "tipo": "atualizacao_pedido",
            "id_pedido": id_pedido,
            "evento": evento,
            "status_descricao": status_legivel,
            "checkout_url": pedidos[id_pedido].get("checkout_url"),
            "pedido": pedidos[id_pedido],
        })

        if evento in ["estoque.indisponivel", "pagamento.recusado"]:
            print(f"Enviando 'pedido.excluido': {id_pedido}...")
            mensagem_json = {"id_pedido": id_pedido}
            payload = assinar_payload(mensagem_json, key_path="private_key.pem")
            ch.basic_publish(
                exchange="eCommerce",
                routing_key="pedido.excluido",
                body=json.dumps(payload),
            )
            pedidos[id_pedido]["status"] = "pedido.excluido"
            pedidos[id_pedido]["status_descricao"] = f"{status_legivel} (Pedido Excluído)"

    ch.basic_ack(delivery_tag=method.delivery_tag)


def iniciar_consumidor():
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host=RABBITMQ_HOST)
    )
    channel = connection.channel()

    channel.exchange_declare(exchange="eCommerce", exchange_type="direct")

    result = channel.queue_declare(queue="fila.principal", exclusive=False)
    queue_name = result.method.queue

    for rk in ORIGEM_CHAVES.keys():
        channel.queue_bind(exchange="eCommerce", queue=queue_name, routing_key=rk)

    print("API Gateway (MS Principal) escutando eventos RabbitMQ...")
    channel.basic_consume(queue=queue_name, on_message_callback=callback_consumidor, auto_ack=False)
    channel.start_consuming()


@asynccontextmanager
async def lifespan(app: FastAPI):
    thread_consumidor = threading.Thread(target=iniciar_consumidor, daemon=True)
    thread_consumidor.start()
    yield


app = FastAPI(title="MS Principal / API Gateway", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# ENDPOINTS REST DO API GATEWAY
# ============================================================================

@app.get("/produtos")
def listar_produtos():
    """
    Consulta a lista de produtos disponíveis diretamente do MS Estoque via REST.
    """
    try:
        resp = requests.get(f"{MS_ESTOQUE_URL}/produtos", timeout=5)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail=f"Erro ao consultar produtos no MS Estoque ({MS_ESTOQUE_URL}): {e}",
        )


@app.get("/pedidos")
def listar_pedidos():
    """Retorna todos os pedidos realizados e seus status atuais."""
    return {"pedidos": pedidos}


@app.post("/pedidos", status_code=201)
def criar_pedido(dados: CriarPedidoRequest):
    """
    Cria um novo pedido e publica 'pedido.criado' no RabbitMQ.
    A URL de checkout será recebida assincronamente via evento 'pagamento.pendente'.
    """
    produtos_filtrados = {
        str(k): int(v) for k, v in dados.produtos.items() if int(v) > 0
    }
    if not produtos_filtrados:
        raise HTTPException(status_code=400, detail="O pedido deve conter ao menos 1 produto.")

    id_pedido = str(uuid.uuid4())[:8]

    pedidos[id_pedido] = {
        "id_pedido": id_pedido,
        "produtos": produtos_filtrados,
        "status": "pedido.criado",
        "status_descricao": MAPA_STATUS_AMIGAVEL["pedido.criado"],
        "checkout_url": None,
    }

    mensagem = {"id_pedido": id_pedido, "produtos": produtos_filtrados}
    publish("pedido.criado", mensagem)
    print(f"\nEnviando 'pedido.criado': {id_pedido}")

    return {
        "mensagem": "Pedido criado com sucesso!",
        "id_pedido": id_pedido,
        "pedido": pedidos[id_pedido],
    }


@app.delete("/pedidos/{id_pedido}")
def excluir_pedido(id_pedido: str):
    """Publica o evento 'pedido.excluido' no RabbitMQ para cancelar o pedido."""
    if id_pedido not in pedidos:
        raise HTTPException(status_code=404, detail="Pedido não encontrado.")

    publish("pedido.excluido", {"id_pedido": id_pedido})
    pedidos[id_pedido]["status"] = "pedido.excluido"
    pedidos[id_pedido]["status_descricao"] = "Pedido Excluído (Manual)"
    print(f"\nEnviando 'pedido.excluido': {id_pedido}")

    notificar_clientes_sse({
        "tipo": "atualizacao_pedido",
        "id_pedido": id_pedido,
        "evento": "pedido.excluido",
        "status_descricao": "Pedido Excluído (Manual)",
        "checkout_url": pedidos[id_pedido]["checkout_url"],
        "pedido": pedidos[id_pedido],
    })

    return {"mensagem": f"Pedido {id_pedido} excluído com sucesso.", "pedido": pedidos[id_pedido]}


@app.post("/interesses")
def registrar_interesse_promocao(dados: InteressePromocaoRequest):
    """
    Registra o interesse de um consumidor (e-mail + categorias)
    publicando o evento 'interesse.promocao' no RabbitMQ.
    """
    email = dados.email.strip()
    categorias = [c.upper() for c in dados.categorias if c.upper() in ("A", "B", "C")]

    if not email or not categorias:
        raise HTTPException(status_code=400, detail="Informe um e-mail válido e ao menos uma categoria (A, B ou C).")

    evento_payload = {
        "email": email,
        "categorias": categorias,
        "acao": "registrar",
    }
    publish("interesse.promocao", evento_payload)
    print(f"\nEnviando 'interesse.promocao' (registrar): {evento_payload}")

    return {
        "mensagem": f"Interesse registrado para {email} nas categorias {', '.join(categorias)}!",
        "dados": evento_payload,
    }


@app.delete("/interesses")
def cancelar_interesse_promocao(dados: InteressePromocaoRequest):
    """
    Cancela o interesse de um consumidor em receber e-mails de promoções
    publicando o evento 'interesse.promocao' (acao='cancelar') no RabbitMQ.
    """
    email = dados.email.strip()
    categorias = [c.upper() for c in dados.categorias if c.upper() in ("A", "B", "C")]

    if not email:
        raise HTTPException(status_code=400, detail="Informe o e-mail para cancelar o interesse.")

    evento_payload = {
        "email": email,
        "categorias": categorias if categorias else ["A", "B", "C"],
        "acao": "cancelar",
    }
    publish("interesse.promocao", evento_payload)
    print(f"\nEnviando 'interesse.promocao' (cancelar): {evento_payload}")

    return {
        "mensagem": f"Interesse cancelado para {email}!",
        "dados": evento_payload,
    }


# ============================================================================
# ENDPOINT SSE (SERVER-SENT EVENTS) PARA NOTIFICAÇÕES EM TEMPO REAL
# ============================================================================

@app.get("/sse/pedidos")
async def sse_acompanhamento_pedidos():
    """
    Mantém conexão SSE aberta com o Frontend para envio de notificações em tempo real
    sobre o status dos pedidos (Estoque Confirmado, Pagamento Aprovado/Recusado, Pedido Enviado).
    """
    fila_cliente = queue.Queue()
    clientes_sse.append(fila_cliente)

    async def event_generator():
        try:
            yield f"data: {json.dumps({'tipo': 'conexao', 'mensagem': 'Conectado ao canal SSE do API Gateway'})}\n\n"
            while True:
                try:
                    evento = fila_cliente.get_nowait()
                    yield f"data: {json.dumps(evento)}\n\n"
                except queue.Empty:
                    await asyncio.sleep(0.2)
        finally:
            if fila_cliente in clientes_sse:
                clientes_sse.remove(fila_cliente)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )


if __name__ == "__main__":
    try:
        uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
    except KeyboardInterrupt:
        sys.exit(0)

        sys.exit(0)
