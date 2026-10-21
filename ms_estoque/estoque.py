import os
import sys
import json
import csv
import threading
from contextlib import asynccontextmanager
from pathlib import Path
import pika
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from seguranca import assinar_payload, validar_envelope

RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "rabbitmq")
CSV_PATH = Path(__file__).parent.parent / "data" / "estoque_produtos.csv"

lock_estoque = threading.Lock()
catalogo_produtos = {}
estoque = {}
reservas = {}


def carregar_estoque():
    with lock_estoque:
        with open(CSV_PATH, newline="", encoding="utf-8") as arq:
            registros = csv.reader(arq)
            cabecalho = next(registros)
            for registro in registros:
                cod = str(registro[0])
                catalogo_produtos[cod] = {
                    "cod_produto": cod,
                    "nom_produto": registro[1],
                    "cod_categoria": registro[2],
                    "vlr_produto": float(registro[3]),
                    "qtd_estoque": int(registro[4]),
                }
                estoque[cod] = int(registro[4])


def persistir_estoque():
    """Persiste os dados atualizados dos produtos em estoque no arquivo CSV."""
    with lock_estoque:
        with open(CSV_PATH, "w", newline="", encoding="utf-8") as arq:
            escritor = csv.writer(arq)
            escritor.writerow(["cod_produto", "nom_produto", "cod_categoria", "vlr_produto", "qtd_estoque"])
            for cod, item in catalogo_produtos.items():
                item["qtd_estoque"] = estoque[cod]
                escritor.writerow([
                    item["cod_produto"],
                    item["nom_produto"],
                    item["cod_categoria"],
                    item["vlr_produto"],
                    item["qtd_estoque"],
                ])


carregar_estoque()


def callback(ch, method, properties, body):
    evento = method.routing_key
    mensagem = validar_envelope(body.decode("utf-8"), key_path="public_keys/principal.pem")

    if mensagem is None:
        print(f"\n [❌] Descartado {evento}: Assinatura digital inválida!")
        ch.basic_ack(delivery_tag=method.delivery_tag)
        return

    id_pedido = mensagem.get("id_pedido")
    print(f"\nRecebido e validado {evento}: {mensagem}")

    if evento == "pedido.criado":
        produtos_solicitados = mensagem.get("produtos", {})

        dispcheck = True
        for produto, quant in produtos_solicitados.items():
            produto_str = str(produto)
            if quant <= 0 or estoque.get(produto_str, 0) < quant:
                dispcheck = False
                break

        if dispcheck:
            valor_total = 0.0
            for produto, quantidade in produtos_solicitados.items():
                produto_str = str(produto)
                estoque[produto_str] -= quantidade
                valor_total += catalogo_produtos[produto_str]["vlr_produto"] * quantidade

            reservas[id_pedido] = produtos_solicitados
            persistir_estoque()

            print(f"\nEnviando 'pedido.estoque_ok': {id_pedido} (Total: R$ {valor_total:.2f})")
            mensagem_json = {
                "id_pedido": id_pedido,
                "valor_total": round(valor_total, 2),
            }
            payload = assinar_payload(mensagem_json, key_path="private_key.pem")

            ch.basic_publish(
                exchange="eCommerce",
                routing_key="pedido.estoque_ok",
                body=json.dumps(payload),
            )
        else:
            print(f"\nEnviando 'estoque.indisponivel': {id_pedido}")
            mensagem_json = {"id_pedido": id_pedido}
            payload = assinar_payload(mensagem_json, key_path="private_key.pem")
            ch.basic_publish(
                exchange="eCommerce",
                routing_key="estoque.indisponivel",
                body=json.dumps(payload),
            )

    elif evento == "pedido.excluido":
        reservados = reservas.get(id_pedido)
        if reservados:
            for produto, quant in reservados.items():
                produto_str = str(produto)
                estoque[produto_str] += quant
            del reservas[id_pedido]
            persistir_estoque()
            print(f"\nRemovido da reserva e estornado ao CSV: {id_pedido}")

    ch.basic_ack(delivery_tag=method.delivery_tag)


def iniciar_consumidor():
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host=RABBITMQ_HOST)
    )
    channel = connection.channel()

    channel.exchange_declare(exchange="eCommerce", exchange_type="direct")

    result = channel.queue_declare(queue="fila.estoque", exclusive=False)
    queue_name = result.method.queue

    routing_keys = ["pedido.criado", "pedido.excluido"]
    for rk in routing_keys:
        channel.queue_bind(exchange="eCommerce", queue=queue_name, routing_key=rk)

    print(f"MS Estoque aguardando eventos RabbitMQ ({ len(estoque) } produtos carregados)...")

    channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=False)
    channel.start_consuming()


@asynccontextmanager
async def lifespan(app: FastAPI):
    thread = threading.Thread(target=iniciar_consumidor, daemon=True)
    thread.start()
    yield


app = FastAPI(title="MS Estoque API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/produtos")
def listar_produtos_disponiveis():
    """Expõe endpoint REST para o MS Gateway consultar os produtos disponíveis em estoque."""
    with lock_estoque:
        disponiveis = [
            {
                "cod_produto": cod,
                "nom_produto": item["nom_produto"],
                "cod_categoria": item["cod_categoria"],
                "vlr_produto": item["vlr_produto"],
                "qtd_estoque": estoque[cod],
            }
            for cod, item in catalogo_produtos.items()
            if estoque[cod] > 0
        ]
    return {"produtos": disponiveis}


if __name__ == "__main__":
    try:
        uvicorn.run(app, host="0.0.0.0", port=8001, log_level="info")
    except KeyboardInterrupt:
        sys.exit(0)