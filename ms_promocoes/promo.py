import pika
import sys
import json
import random
import time

def main():
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host='rabbitmq'))
    channel = connection.channel()

    channel.exchange_declare(exchange='Promo', exchange_type='topic')

    categorias = ['A', 'B', 'C']

    while True:
        categoria = random.choice(categorias)
        desconto = random.randint(10, 60)
            
        routing_key = f'promocao.categoria.{categoria}'
            
        mensagem = {
            "categoria": categoria,
            "desconto": f"{desconto}%",
            "mensagem": f"Desconto lançado na categoria {categoria}!"
        }

        channel.basic_publish(
            exchange='Promo',
            routing_key=routing_key,
            body=json.dumps(mensagem)
        )
        print(f"\nEnviando {routing_key}:{mensagem}")
            
        time.sleep(random.uniform(3, 8))

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)