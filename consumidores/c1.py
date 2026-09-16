import pika
import sys
import json
from seguranca import validar_envelope

def callback(ch, method, properties, body):
    mensagem = validar_envelope(body.decode("utf-8"), key_path="public_keys/promocoes.pem")

    if mensagem is None:
        print(
            f"\n [❌] Promoção descartada na routing key {method.routing_key}:"
            " Assinatura digital inválida!"
        )
        return
    print(f"\nRecebido (Routing Key: {method.routing_key}):")
    print(f"\n- Categoria: {mensagem.get('categoria')}")
    print(f"\n- Desconto: {mensagem.get('desconto')}")
    print(f"\n- Detalhes: {mensagem.get('mensagem')}")

def main():
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host='rabbitmq'))
    channel = connection.channel()

    channel.exchange_declare(exchange='Promo', exchange_type='topic')

    result = channel.queue_declare(queue='fila.c1', exclusive=False)
    queue_name = result.method.queue

    routing_keys = ['promocao.categoria.A', 'promocao.categoria.B']
    for rk in routing_keys:
        channel.queue_bind(exchange='Promo', queue=queue_name, routing_key=rk)

    print('C1 esperando promoções categoria A e B.')

    channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)
    channel.start_consuming()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)