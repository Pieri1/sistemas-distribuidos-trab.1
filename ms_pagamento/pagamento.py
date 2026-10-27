import os
import sys
import json
import threading
from contextlib import asynccontextmanager
import pika
import requests
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from seguranca import assinar_payload, validar_envelope

RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "rabbitmq")
MOCK_PAGAMENTO_URL = os.getenv("MOCK_PAGAMENTO_URL", "http://localhost:8003")
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "http://localhost:8002/webhook/pagamento")

cobrancas_registradas = {}


class WebhookPagamentoPayload(BaseModel):
    id_pedido: str
    status: str  # "APROVADO" ou "RECUSADO"


def publicar_evento(routing_key: str, mensagem_json: dict):
    """Abre conexão com o RabbitMQ, assina o payload com a chave privada e publica o evento."""
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host=RABBITMQ_HOST)
    )
    channel = connection.channel()
    channel.exchange_declare(exchange="eCommerce", exchange_type="direct")

    payload = assinar_payload(mensagem_json, key_path="private_key.pem")
    channel.basic_publish(
        exchange="eCommerce",
        routing_key=routing_key,
        body=json.dumps(payload),
    )
    connection.close()


def callback(ch, method, properties, body):
    evento = method.routing_key
    mensagem = validar_envelope(body.decode("utf-8"), key_path="public_keys/estoque.pem")

    if mensagem is None:
        print(f"\n [❌] Descartado {evento}: Assinatura digital inválida!")
        ch.basic_ack(delivery_tag=method.delivery_tag)
        return

    id_pedido = mensagem.get("id_pedido")
    valor_total = mensagem.get("valor_total", 0.0)
    print(f"\nRecebido e validado {evento}: {mensagem}")

    if evento == "pedido.estoque_ok":
        try:
            dados_cobranca = {
                "id_pedido": id_pedido,
                "valor": valor_total,
                "webhook_url": WEBHOOK_URL,
            }
            resposta = requests.post(
                f"{MOCK_PAGAMENTO_URL}/cobrancas",
                json=dados_cobranca,
                timeout=5,
            )
            resposta.raise_for_status()
            retorno = resposta.json()
            checkout_url = retorno.get("checkout_url")
            cobrancas_registradas[id_pedido] = checkout_url
            print(f"\n[MS Pagamento] Cobrança solicitada ao Mock para o pedido {id_pedido}!")
            print(f" -> URL de Checkout recebida do Mock: {checkout_url}")
            print(f" -> Aguardando Webhook em: {WEBHOOK_URL}")

            print(f"Enviando 'pagamento.pendente': {id_pedido}")
            publicar_evento(
                "pagamento.pendente",
                {
                    "id_pedido": id_pedido,
                    "checkout_url": checkout_url,
                },
            )
        except Exception as e:
            print(f"\n [❌] Erro ao solicitar cobrança ao Mock de Pagamento: {e}")

    ch.basic_ack(delivery_tag=method.delivery_tag)


def iniciar_consumidor():
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host=RABBITMQ_HOST)
    )
    channel = connection.channel()

    channel.exchange_declare(exchange="eCommerce", exchange_type="direct")

    result = channel.queue_declare(queue="fila.pagamento", exclusive=False)
    queue_name = result.method.queue

    channel.queue_bind(exchange="eCommerce", queue=queue_name, routing_key="pedido.estoque_ok")

    print("MS Pagamento aguardando eventos 'pedido.estoque_ok' no RabbitMQ...")

    channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=False)
    channel.start_consuming()


@asynccontextmanager
async def lifespan(app: FastAPI):
    thread = threading.Thread(target=iniciar_consumidor, daemon=True)
    thread.start()
    yield


app = FastAPI(title="MS Pagamento API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/webhook/pagamento")
def receber_webhook(dados: WebhookPagamentoPayload):
    """
    Endpoint HTTP que recebe o Webhook do Mock de Pagamento com o status APROVADO ou RECUSADO
    e publica no RabbitMQ 'pagamento.aprovado' ou 'pagamento.recusado'.
    """
    id_pedido = dados.id_pedido
    status = dados.status.upper()

    print(f"\n[Webhook Recebido] Pedido: {id_pedido} | Status: {status}")

    if status == "APROVADO":
        print(f"Enviando 'pagamento.aprovado': {id_pedido}")
        publicar_evento("pagamento.aprovado", {"id_pedido": id_pedido})
        return {"id_pedido": id_pedido, "evento_publicado": "pagamento.aprovado"}
    elif status == "RECUSADO":
        print(f"Enviando 'pagamento.recusado': {id_pedido}")
        publicar_evento("pagamento.recusado", {"id_pedido": id_pedido})
        return {"id_pedido": id_pedido, "evento_publicado": "pagamento.recusado"}
    else:
        raise HTTPException(status_code=400, detail="Status inválido. Use APROVADO ou RECUSADO.")


if __name__ == "__main__":
    try:
        uvicorn.run(app, host="0.0.0.0", port=8002, log_level="info")
    except KeyboardInterrupt:
        sys.exit(0)