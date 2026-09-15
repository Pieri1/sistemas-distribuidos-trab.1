import pika
import sys
import json
import time

def callback(ch, method, properties, body):
    evento = method.routing_key
    mensagem = json.loads(body)
    id_pedido = mensagem.get("id_pedido")
    
    print(f"\nRecebido {evento}: {mensagem}")

    if evento == "pagamento.aprovado":
        time.sleep(2)

        print(f"\nEnviando 'pedido.enviado': {id_pedido}")
        ch.basic_publish(
            exchange='eCommerce',
            routing_key='pedido.enviado',
            body=json.dumps({"id_pedido": id_pedido})
        )

def main():
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host='rabbitmq'))
    channel = connection.channel()

    channel.exchange_declare(exchange='eCommerce', exchange_type='direct')

    result = channel.queue_declare(queue='fila_entrega', exclusive=False)
    queue_name = result.method.queue

    channel.queue_bind(exchange='eCommerce', queue=queue_name, routing_key='pagamento.aprovado')

    channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)
    channel.start_consuming()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)