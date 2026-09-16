import pika
import sys
import json
import random
import time
from seguranca import assinar_payload

def main():
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host='rabbitmq'))
    channel = connection.channel()

    channel.exchange_declare(exchange='Promo', exchange_type='topic')

    categorias = ['A', 'B', 'C']

    while True:
        categoria = random.choice(categorias)
        desconto = random.randint(5, 15)
            
        routing_key = f'promocao.categoria.{categoria}'
            
        mensagem_json = {
            "categoria": categoria,
            "desconto": f"{desconto}%",
            "mensagem": f"Desconto lançado na categoria {categoria}!"
        }

        payload = assinar_payload(mensagem_json, key_path="private_key.pem")

        channel.basic_publish(
            exchange='Promo',
            routing_key=routing_key,
            body=json.dumps(payload)
        )
        print(f"\nEnviando {routing_key}:{mensagem_json}")
            
        time.sleep(random.uniform(15, 30))

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)