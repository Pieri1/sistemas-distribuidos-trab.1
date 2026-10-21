from fastapi import FastAPI
from pydantic import BaseModel
import requests

# Este servidor simula o "MS Pagamento" na porta 8001
app = FastAPI(title="Tutorial 2 - Meu Serviço (Receptor de Webhook)")

URL_MOCK_PAGAMENTO = "http://localhost:8002"
MINHA_URL_WEBHOOK = "http://localhost:8001/webhook/pagamento"


class NotificacaoWebhook(BaseModel):
    id_pedido: str
    status: str  # "APROVADO" ou "RECUSADO"


# 1. Simula o momento em que o MS Pagamento consome "pedido.estoque_ok" e pede ao Mock uma URL de checkout
@app.post("/iniciar-pagamento/{id_pedido}")
def iniciar_pagamento(id_pedido: str, valor: float = 150.0):
    """
    Solicita ao Mock de Pagamento a criação de uma cobrança,
    enviando a nossa URL de Webhook para receber a resposta depois.
    """
    dados_cobranca = {
        "id_pedido": id_pedido,
        "valor": valor,
        "webhook_url": MINHA_URL_WEBHOOK,
    }
    resposta = requests.post(f"{URL_MOCK_PAGAMENTO}/cobrancas", json=dados_cobranca)
    dados_retorno = resposta.json()

    print(f"[MS Pagamento] Cobrança solicitada! Abra no navegador: {dados_retorno['checkout_url']}")
    return {
        "instrucao": "Abra a checkout_url abaixo no seu navegador e clique em Aprovar ou Recusar!",
        "checkout_url": dados_retorno["checkout_url"],
    }


# 2. ENDPOINT DE WEBHOOK: O Mock de Pagamento chamará esta rota quando o usuário clicar no botão!
@app.post("/webhook/pagamento")
def receber_webhook_pagamento(notificacao: NotificacaoWebhook):
    """
    Recebe o callback (Webhook) do Mock de Pagamento com o status APROVADO ou RECUSADO.
    No Trabalho 2, é aqui dentro que o MS Pagamento publicará no RabbitMQ:
    'pagamento.aprovado' ou 'pagamento.recusado'!
    """
    print("\n" + "=" * 50)
    print(f"🔔 [WEBHOOK RECEBIDO!] Pedido: {notificacao.id_pedido} | Status: {notificacao.status}")
    if notificacao.status == "APROVADO":
        print("-> No Trabalho 2, aqui você publica 'pagamento.aprovado' no RabbitMQ!")
    else:
        print("-> No Trabalho 2, aqui você publica 'pagamento.recusado' no RabbitMQ!")
    print("=" * 50 + "\n")

    return {"recebido": True, "id_pedido": notificacao.id_pedido, "status": notificacao.status}

