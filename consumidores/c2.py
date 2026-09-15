import pika
import sys
import json

def callback(ch, method, properties, body):
    mensagem = json.loads(body)
    print(f"\nRecebido (Routing Key: {method.routing_key}):")
    print(f"\n- Categoria: {mensagem.get('categoria')}")
    print(f"\n- Desconto: {mensagem.get('desconto')}")
    print(f"\n- Detalhes: {mensagem.get('mensagem')}")

def main():
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host='rabbitmq'))
    channel = connection.channel()

    channel.exchange_declare(exchange='Promo', exchange_type='topic')

    result = channel.queue_declare(queue='fila_c2', exclusive=False)
    queue_name = result.method.queue

    channel.queue_bind(exchange='Promo', queue=queue_name, routing_key='promocao.categoria.*')

    print('C2 esperando todas as promoções.')

    channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)
    channel.start_consuming()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)