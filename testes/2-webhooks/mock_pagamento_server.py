from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import requests

# Este servidor simula o "Mock de Pagamento (Sistema Externo)" na porta 8002
app = FastAPI(title="Tutorial 2 - Mock de Pagamento Externo")

# Armazena as cobranças pendentes em memória
cobrancas = {}


class SolicitacaoCobranca(BaseModel):
    id_pedido: str
    valor: float
    webhook_url: str  # URL para onde este Mock enviará o POST quando o usuário clicar no botão!


# 1. Endpoint chamado pelo MS Pagamento para gerar o link de pagamento
@app.post("/cobrancas")
def criar_cobranca(dados: SolicitacaoCobranca):
    cobrancas[dados.id_pedido] = {
        "valor": dados.valor,
        "webhook_url": dados.webhook_url,
        "status": "PENDENTE",
    }
    # Gera a URL que o Frontend abrirá em uma nova aba do navegador
    checkout_url = f"http://localhost:8002/checkout/{dados.id_pedido}"
    print(f"[Mock Pagamento] Cobrança criada para pedido {dados.id_pedido}. URL: {checkout_url}")
    return {"id_pedido": dados.id_pedido, "checkout_url": checkout_url}


# 2. Página HTML aberta no navegador do usuário (nova aba) para aprovar ou recusar
@app.get("/checkout/{id_pedido}", response_class=HTMLResponse)
def pagina_checkout(id_pedido: str):
    if id_pedido not in cobrancas:
        raise HTTPException(status_code=404, detail="Cobrança não encontrada")

    info = cobrancas[id_pedido]
    return f"""
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <title>Checkout - Pedido {id_pedido}</title>
        <style>
            body {{ font-family: Arial, sans-serif; max-width: 420px; margin: 60px auto; text-align: center; border: 1px solid #ddd; padding: 24px; border-radius: 12px; }}
            button {{ padding: 12px 20px; margin: 10px; font-size: 16px; cursor: pointer; border: none; border-radius: 6px; color: white; }}
            .aprovar {{ background-color: #28a745; }}
            .recusar {{ background-color: #dc3545; }}
        </style>
    </head>
    <body>
        <h2>💳 Mock de Pagamento</h2>
        <p><strong>Pedido:</strong> {id_pedido}</p>
        <p><strong>Valor:</strong> R$ {info['valor']:.2f}</p>
        <p><strong>Status atual:</strong> <span id="status">{info['status']}</span></p>
        <div>
            <button class="aprovar" onclick="decidir('APROVADO')">✅ Pagamento Aprovado</button>
            <button class="recusar" onclick="decidir('RECUSADO')">❌ Pagamento Recusado</button>
        </div>
        <p id="msg"></p>
        <script>
            async function decidir(novoStatus) {{
                const resp = await fetch('/checkout/{id_pedido}/decidir?status=' + novoStatus, {{ method: 'POST' }});
                const dados = await resp.json();
                document.getElementById('status').innerText = novoStatus;
                document.getElementById('msg').innerText = dados.mensagem;
            }}
        </script>
    </body>
    </html>
    """


# 3. Rota acionada pelo clique do botão na página HTML acima -> Dispara o WEBHOOK!
@app.post("/checkout/{id_pedido}/decidir")
def decidir_pagamento(id_pedido: str, status: str):
    if id_pedido not in cobrancas:
        raise HTTPException(status_code=404, detail="Cobrança não encontrada")

    cobrancas[id_pedido]["status"] = status
    webhook_url = cobrancas[id_pedido]["webhook_url"]

    # AQUI ACONTECE O WEBHOOK:
    # O Mock de Pagamento faz uma requisição HTTP POST para a URL que o MS Pagamento informou!
    payload_webhook = {
        "id_pedido": id_pedido,
        "status": status,  # "APROVADO" ou "RECUSADO"
    }
    print(f"[Mock Pagamento] Disparando Webhook POST para {webhook_url} -> {payload_webhook}")
    resposta = requests.post(webhook_url, json=payload_webhook)

    return {
        "mensagem": f"Webhook enviado para o MS Pagamento! Resposta HTTP: {resposta.status_code}",
        "detalhes": resposta.json(),
    }

