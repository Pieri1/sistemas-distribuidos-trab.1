import asyncio
import json
import queue
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

app = FastAPI(title="Tutorial 3 - Server-Sent Events (SSE)")

# Habilita CORS para permitir que o Frontend (Node/Express) conecte via EventSource
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Lista de filas (uma fila thread-safe por navegador/cliente conectado ao SSE)
# Usamos queue.Queue() padrão do Python porque ela funciona perfeitamente
# tanto dentro do FastAPI quanto dentro da thread do RabbitMQ (pika)!
clientes_sse: list[queue.Queue] = []


def enviar_para_todos_clientes_sse(dados_evento: dict):
    """
    Coloca uma mensagem na fila de todos os clientes conectados via SSE.
    No Trabalho 2, basta chamar esta função dentro do seu `callback_consumidor` do RabbitMQ!
    """
    for fila_cliente in list(clientes_sse):
        fila_cliente.put(dados_evento)


# 1. ROTA SSE: O navegador se conecta aqui usando `new EventSource('http://localhost:8003/sse/pedidos')`
@app.get("/sse/pedidos")
async def stream_eventos_pedidos():
    """Mantém a conexão HTTP aberta e envia eventos no formato text/event-stream."""
    fila_deste_cliente = queue.Queue()
    clientes_sse.append(fila_deste_cliente)

    async def gerador_de_eventos():
        try:
            # Envia uma mensagem inicial assim que o cliente se conecta
            boas_vindas = {"tipo": "conexao", "mensagem": "Conectado ao canal SSE com sucesso!"}
            yield f"data: {json.dumps(boas_vindas)}\n\n"

            while True:
                # Verifica se chegou algum evento na fila (sem travar o loop assíncrono do FastAPI)
                try:
                    evento = fila_deste_cliente.get_nowait()
                    # Formato oficial do SSE: "data: <json>\n\n"
                    yield f"data: {json.dumps(evento)}\n\n"
                except queue.Empty:
                    # Se não há evento novo, aguarda 0.2s e envia um comentário keep-alive opcional
                    await asyncio.sleep(0.2)
        finally:
            # Quando o usuário fecha a aba do navegador, removemos a fila dele da lista
            if fila_deste_cliente in clientes_sse:
                clientes_sse.remove(fila_deste_cliente)

    return StreamingResponse(
        gerador_de_eventos(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )


# 2. Rota auxiliar apenas para você testar o disparo de eventos pelo Swagger (/docs) ou curl
@app.post("/simular-evento")
def simular_evento_rabbitmq(id_pedido: str = "ped-101", status: str = "Estoque Confirmado"):
    """
    Simula a chegada de uma mensagem do RabbitMQ e empurra para o navegador via SSE.
    """
    novo_evento = {
        "id_pedido": id_pedido,
        "status": status,
    }
    enviar_para_todos_clientes_sse(novo_evento)
    return {
        "mensagem": "Evento enviado para todos os clientes SSE conectados!",
        "clientes_conectados": len(clientes_sse),
        "evento": novo_evento,
    }

