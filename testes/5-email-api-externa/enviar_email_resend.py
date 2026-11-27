import os
import requests

# URL oficial da API REST do Resend
RESEND_API_URL = "https://api.resend.com/emails"

# Lê a chave de API das variáveis de ambiente (ou deixe vazio para rodar em modo de simulação)
RESEND_API_KEY = os.getenv("RESEND_API_KEY", "")
EMAIL_DESTINO = os.getenv("EMAIL_DESTINO", "cliente@exemplo.com")


def disparar_email_promocao(email_cliente: str, categoria: str, desconto: str):
    """
    Envia um e-mail de promoção consumindo a API REST externa do Resend.
    """
    # 1. Cabeçalhos HTTP exigidos pela API do Resend
    headers = {
        "Authorization": f"Bearer {RESEND_API_KEY}",
        "Content-Type": "application/json",
    }

    # 2. Corpo JSON da requisição
    payload = {
        "from": "E-Commerce UTFPR <onboarding@resend.dev>",
        "to": [email_cliente],
        "subject": f"🔥 Promoção Imperdível na Categoria {categoria} ({desconto} OFF)!",
        "html": f"""
            <h2>Olá! Temos uma oferta especial para você 🎁</h2>
            <p>Você cadastrou interesse na <strong>Categoria {categoria}</strong>.</p>
            <p>Aproveite agora <strong>{desconto} de desconto</strong> em todos os produtos dessa categoria!</p>
        """,
    }

    # Se o aluno ainda não configurou a RESEND_API_KEY, mostramos como a requisição seria enviada
    if not RESEND_API_KEY:
        print("⚠️ [MODO SIMULAÇÃO] Variável RESEND_API_KEY não definida.")
        print(f"-> Seria enviado um POST para: {RESEND_API_URL}")
        print(f"-> Destinatário: {email_cliente} | Categoria: {categoria} | Desconto: {desconto}")
        print(f"-> Payload JSON:\n{payload}\n")
        return

    # 3. Chamada HTTP POST real para a API Externa
    resposta = requests.post(RESEND_API_URL, headers=headers, json=payload)

    if resposta.status_code in (200, 201):
        print(f"✅ E-mail enviado com sucesso para {email_cliente}! ID: {resposta.json().get('id')}")
    else:
        print(f"❌ Falha ao enviar e-mail ({resposta.status_code}): {resposta.text}")


if __name__ == "__main__":
    # Simulando o que o MS Promoções fará quando sortear uma promoção da Categoria A:
    disparar_email_promocao(
        email_cliente=EMAIL_DESTINO,
        categoria="A",
        desconto="15%",
    )

