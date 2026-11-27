import os
import sys
import requests
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

PUBLIC_MOCK_URL = os.getenv("PUBLIC_MOCK_URL", "http://localhost:8003")
DEFAULT_WEBHOOK_URL = os.getenv("DEFAULT_WEBHOOK_URL", "http://localhost:8002/webhook/pagamento")

app = FastAPI(title="Mock de Pagamento (Sistema Externo)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

cobrancas = {}


class SolicitacaoCobranca(BaseModel):
    id_pedido: str
    valor: float = 0.0
    webhook_url: str


@app.post("/cobrancas")
def criar_cobranca(dados: SolicitacaoCobranca):
    """
    Processa a solicitação de cobrança do MS Pagamento via REST,
    armazenando a URL de Webhook para retorno e gerando a URL de checkout.
    """
    cobrancas[dados.id_pedido] = {
        "id_pedido": dados.id_pedido,
        "valor": dados.valor,
        "webhook_url": dados.webhook_url,
        "status": "PENDENTE",
    }
    checkout_url = f"{PUBLIC_MOCK_URL}/checkout/{dados.id_pedido}"
    print(f"\n[Mock de Pagamento] Cobrança criada para o pedido {dados.id_pedido} (R$ {dados.valor:.2f})")
    print(f" -> URL de Checkout: {checkout_url}")
    print(f" -> URL de Webhook registrada: {dados.webhook_url}")
    return {
        "id_pedido": dados.id_pedido,
        "checkout_url": checkout_url,
        "status": "PENDENTE",
    }


@app.get("/checkout/{id_pedido}", response_class=HTMLResponse)
def pagina_checkout(id_pedido: str):
    """
    Abre uma página no navegador onde o usuário clica nos botões
    'Pagamento Aprovado' ou 'Pagamento Recusado'.
    """
    cobranca = cobrancas.get(id_pedido)

    # Caso a aba do navegador tenha aberto alguns milissegundos antes de o MS Pagamento
    # concluir a chamada REST ao Mock, exibimos uma tela que atualiza automaticamente em 1s.
    if cobranca is None:
        return f"""
        <!DOCTYPE html>
        <html lang="pt-BR">
        <head>
            <meta charset="UTF-8">
            <meta http-equiv="refresh" content="1">
            <title>Preparando Checkout - Pedido {id_pedido}</title>
            <style>
                body {{ font-family: 'Segoe UI', Arial, sans-serif; background: #f4f6f9; display: flex; align-items: center; justify-content: center; height: 100vh; margin: 0; }}
                .box {{ background: white; padding: 32px; border-radius: 12px; box-shadow: 0 4px 16px rgba(0,0,0,0.08); text-align: center; max-width: 420px; }}
            </style>
        </head>
        <body>
            <div class="box">
                <h2>⏳ Processando Reserva de Estoque...</h2>
                <p>Aguardando liberação da cobrança para o pedido <strong>#{id_pedido}</strong>.</p>
                <p><small>Se o estoque for indisponível, o pedido será cancelado automaticamente.</small></p>
            </div>
        </body>
        </html>
        """

    valor_formatado = f"R$ {cobranca['valor']:.2f}"
    status_atual = cobranca["status"]

    return f"""
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <title>Mock de Pagamento - Pedido #{id_pedido}</title>
        <style>
            body {{
                font-family: 'Segoe UI', Arial, sans-serif;
                background: #f1f5f9;
                display: flex;
                align-items: center;
                justify-content: center;
                min-height: 100vh;
                margin: 0;
                color: #1e293b;
            }}
            .card {{
                background: #ffffff;
                padding: 32px;
                border-radius: 14px;
                box-shadow: 0 10px 25px rgba(0, 0, 0, 0.08);
                max-width: 440px;
                width: 100%;
                text-align: center;
            }}
            h2 {{ margin-top: 0; color: #0f172a; }}
            .info {{
                background: #f8fafc;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                padding: 16px;
                margin: 20px 0;
                text-align: left;
            }}
            .info p {{ margin: 8px 0; font-size: 15px; }}
            .botoes {{ display: flex; gap: 12px; justify-content: center; margin-top: 20px; }}
            button {{
                flex: 1;
                padding: 14px 16px;
                font-size: 15px;
                font-weight: 600;
                border: none;
                border-radius: 8px;
                cursor: pointer;
                color: white;
                transition: opacity 0.2s;
            }}
            button:disabled {{ opacity: 0.5; cursor: not-allowed; }}
            .btn-aprovar {{ background-color: #16a34a; }}
            .btn-aprovar:hover:not(:disabled) {{ background-color: #15803d; }}
            .btn-recusar {{ background-color: #dc2626; }}
            .btn-recusar:hover:not(:disabled) {{ background-color: #b91c1c; }}
            #resultado {{
                margin-top: 18px;
                padding: 12px;
                border-radius: 8px;
                font-weight: 600;
                display: none;
            }}
        </style>
    </head>
    <body>
        <div class="card">
            <h2>💳 Provedor Externo de Pagamento</h2>
            <p>Simulação de Checkout para conclusão da compra</p>
            <div class="info">
                <p><strong>ID do Pedido:</strong> #{id_pedido}</p>
                <p><strong>Valor Total:</strong> {valor_formatado}</p>
                <p><strong>Status:</strong> <span id="status-texto">{status_atual}</span></p>
                <p><strong>Webhook destino:</strong> <small>{cobranca['webhook_url']}</small></p>
            </div>
            <div class="botoes">
                <button id="btn-aprovar" class="btn-aprovar" onclick="enviarDecisao('APROVADO')">
                    ✅ Pagamento Aprovado
                </button>
                <button id="btn-recusar" class="btn-recusar" onclick="enviarDecisao('RECUSADO')">
                    ❌ Pagamento Recusado
                </button>
            </div>
            <div id="resultado"></div>
        </div>

        <script>
            async function enviarDecisao(decisao) {{
                document.getElementById('btn-aprovar').disabled = true;
                document.getElementById('btn-recusar').disabled = true;
                const box = document.getElementById('resultado');
                box.style.display = 'block';
                box.style.background = '#e0f2fe';
                box.style.color = '#0369a1';
                box.textContent = 'Enviando Webhook para o MS Pagamento...';

                try {{
                    const resp = await fetch('/checkout/{id_pedido}/decidir', {{
                        method: 'POST',
                        headers: {{ 'Content-Type': 'application/json' }},
                        body: JSON.stringify({{ status: decisao }})
                    }});
                    const data = await resp.json();
                    document.getElementById('status-texto').textContent = decisao;
                    box.style.background = decisao === 'APROVADO' ? '#dcfce7' : '#fee2e2';
                    box.style.color = decisao === 'APROVADO' ? '#166534' : '#991b1b';
                    box.textContent = data.mensagem;
                }} catch (err) {{
                    box.style.background = '#fee2e2';
                    box.style.color = '#991b1b';
                    box.textContent = 'Erro ao comunicar com o servidor de pagamento.';
                    document.getElementById('btn-aprovar').disabled = false;
                    document.getElementById('btn-recusar').disabled = false;
                }}
            }}
        </script>
    </body>
    </html>
    """


class DecisaoCheckout(BaseModel):
    status: str  # "APROVADO" ou "RECUSADO"


@app.post("/checkout/{id_pedido}/decidir")
def processar_decisao(id_pedido: str, decisao: DecisaoCheckout):
    """
    Quando o usuário clica no botão da página, dispara uma chamada HTTP POST (Webhook)
    para a URL informada pelo MS Pagamento.
    """
    cobranca = cobrancas.get(id_pedido)
    if not cobranca:
        cobranca = {
            "id_pedido": id_pedido,
            "valor": 0.0,
            "webhook_url": DEFAULT_WEBHOOK_URL,
            "status": "PENDENTE",
        }
        cobrancas[id_pedido] = cobranca

    status_escolhido = decisao.status.upper()
    cobranca["status"] = status_escolhido
    webhook_url = cobranca["webhook_url"]

    payload_webhook = {
        "id_pedido": id_pedido,
        "status": status_escolhido,
    }

    print(f"\n[Mock de Pagamento] Usuário escolheu '{status_escolhido}' para o pedido {id_pedido}.")
    print(f" -> Disparando HTTP POST (Webhook) para: {webhook_url}")

    try:
        resp = requests.post(webhook_url, json=payload_webhook, timeout=5)
        resp.raise_for_status()
        return {
            "mensagem": f"Pagamento {status_escolhido}! Webhook enviado ao MS Pagamento (você já pode voltar à aba da loja).",
            "webhook_response": resp.json(),
        }
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Falha ao enviar Webhook: {e}")


if __name__ == "__main__":
    try:
        uvicorn.run(app, host="0.0.0.0", port=8003, log_level="info")
    except KeyboardInterrupt:
        sys.exit(0)

