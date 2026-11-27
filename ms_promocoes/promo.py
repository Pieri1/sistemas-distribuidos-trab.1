import os
import sys
import json
import random
import time
import threading
import pika
import requests
from seguranca import assinar_payload, validar_envelope
from dotenv import load_dotenv

load_dotenv()

RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "rabbitmq")
RESEND_API_URL = "https://api.resend.com/emails"
RESEND_API_KEY = os.getenv("RESEND_API_KEY")
RESEND_FROM = os.getenv("RESEND_FROM", "E-Commerce UTFPR <onboarding@resend.dev>")

lock_interesses = threading.Lock()
interesses_por_categoria = {
    "A": set(),
    "B": set(),
    "C": set(),
}


def enviar_email_promocao(email_destino: str, categoria: str, desconto: str, mensagem_promo: str):
    """
    Integra-se com a API Externa de E-mail (Resend) via HTTP REST (POST)
    para disparar notificações de promoções aos consumidores cadastrados.
    """
    payload_email = {
        "from": RESEND_FROM,
        "to": [email_destino],
        "subject": f"Oferta Especial - Categoria {categoria} com {desconto} OFF!",
        "html": (
            f"<h2>Promoção na Categoria {categoria}!</h2>"
            f"<p>{mensagem_promo}</p>"
            f"<p>Desconto exclusivo de <strong>{desconto}</strong> para você!</p>"
        ),
    }

    if not RESEND_API_KEY:
        print(
            f" [📧 E-mail Simulado - defina RESEND_API_KEY para envio real] "
            f"Para: {email_destino} | Categoria: {categoria} ({desconto})"
        )
        return

    headers = {
        "Authorization": f"Bearer {RESEND_API_KEY}",
        "Content-Type": "application/json",
    }

    try:
        resp = requests.post(RESEND_API_URL, headers=headers, json=payload_email, timeout=10)
        if resp.status_code in (200, 201):
            print(f" [📧✓] E-mail enviado via Resend para {email_destino} (ID: {resp.json().get('id')})")
        else:
            print(f" [📧❌] Resend retornou {resp.status_code} para {email_destino}: {resp.text}")
    except Exception as e:
        print(f" [📧❌] Erro ao chamar API de e-mail para {email_destino}: {e}")


def callback_interesse(ch, method, properties, body):
    evento = method.routing_key
    mensagem = validar_envelope(body.decode("utf-8"), key_path="public_keys/principal.pem")

    if mensagem is None:
        print(f"\n [❌] Descartado {evento}: Assinatura digital inválida!")
        ch.basic_ack(delivery_tag=method.delivery_tag)
        return

    email = mensagem.get("email", "").strip()
    categorias = mensagem.get("categorias", [])
    acao = mensagem.get("acao", "registrar")

    print(f"\nRecebido e validado '{evento}': {mensagem}")

    if email:
        with lock_interesses:
            if acao == "cancelar":
                categorias_alvo = categorias if categorias else ["A", "B", "C"]
                for cat in categorias_alvo:
                    cat_upper = cat.upper()
                    if cat_upper in interesses_por_categoria:
                        interesses_por_categoria[cat_upper].discard(email)
                print(f" [🔕] Interesse cancelado para {email} nas categorias: {categorias_alvo}")
            else:
                for cat in categorias:
                    cat_upper = cat.upper()
                    if cat_upper in interesses_por_categoria:
                        interesses_por_categoria[cat_upper].add(email)
                print(f" [🔔] Interesse registrado para {email} nas categorias: {categorias}")

            resumo = {k: list(v) for k, v in interesses_por_categoria.items()}
            print(f" -> Base atual de inscritos: {resumo}")

    ch.basic_ack(delivery_tag=method.delivery_tag)


def iniciar_consumidor_interesses():
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host=RABBITMQ_HOST)
    )
    channel = connection.channel()

    channel.exchange_declare(exchange="eCommerce", exchange_type="direct")

    result = channel.queue_declare(queue="fila.promocoes", exclusive=False)
    queue_name = result.method.queue

    channel.queue_bind(exchange="eCommerce", queue=queue_name, routing_key="interesse.promocao")

    print("MS Promoções aguardando eventos 'interesse.promocao'...")
    channel.basic_consume(queue=queue_name, on_message_callback=callback_interesse, auto_ack=False)
    channel.start_consuming()


def gerador_de_promocoes():
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host=RABBITMQ_HOST)
    )
    channel = connection.channel()

    channel.exchange_declare(exchange="Promo", exchange_type="topic")

    categorias = ["A", "B", "C"]

    while True:
        categoria = random.choice(categorias)
        desconto = f"{random.randint(5, 15)}%"
        routing_key = f"promocao.categoria.{categoria}"

        mensagem_json = {
            "categoria": categoria,
            "desconto": desconto,
            "mensagem": f"Desconto lançado na categoria {categoria}!",
        }

        payload = assinar_payload(mensagem_json, key_path="private_key.pem")

        channel.basic_publish(
            exchange="Promo",
            routing_key=routing_key,
            body=json.dumps(payload),
        )
        print(f"\n[Promoção Gerada] {routing_key}: {mensagem_json}")

        with lock_interesses:
            destinatarios = list(interesses_por_categoria.get(categoria, set()))

        if destinatarios:
            print(f" -> Notificando {len(destinatarios)} consumidor(es) interessado(s) na categoria {categoria}...")
            for email_cliente in destinatarios:
                enviar_email_promocao(
                    email_destino=email_cliente,
                    categoria=categoria,
                    desconto=desconto,
                    mensagem_promo=mensagem_json["mensagem"],
                )
        else:
            print(f" -> Nenhum e-mail inscrito na categoria {categoria} no momento.")

        time.sleep(random.uniform(15, 25))


if __name__ == "__main__":
    thread_interesses = threading.Thread(target=iniciar_consumidor_interesses, daemon=True)
    thread_interesses.start()

    try:
        gerador_de_promocoes()
    except KeyboardInterrupt:
        sys.exit(0)