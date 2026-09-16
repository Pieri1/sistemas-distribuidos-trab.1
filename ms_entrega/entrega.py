import pika
import sys
import json
import time
from seguranca import assinar_payload, validar_envelope

def callback(ch, method, properties, body):
    evento = method.routing_key

    mensagem = validar_envelope(body.decode("utf-8"), key_path="public_keys/pagamento.pem")

    if mensagem is None:
        print(f"\n [❌] Descartado {evento}: Assinatura digital inválida!")
        ch.basic_ack(delivery_tag=method.delivery_tag)
        return

    id_pedido = mensagem.get("id_pedido")
    print(f"\nRecebido e validado {evento}: {mensagem}")

    if evento == "pagamento.aprovado":
        time.sleep(2)

        print(f"\nEnviando 'pedido.enviado': {id_pedido}")
        mensagem_json = {"id_pedido": id_pedido}
        payload = assinar_payload(mensagem_json, key_path="private_key.pem")

        ch.basic_publish(
            exchange='eCommerce',
            routing_key='pedido.enviado',
            body=json.dumps(payload)
        )

    ch.basic_ack(delivery_tag=method.delivery_tag)

def main():
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host='rabbitmq'))
    channel = connection.channel()

    channel.exchange_declare(exchange='eCommerce', exchange_type='direct')

    result = channel.queue_declare(queue='fila.entrega', exclusive=False)
    queue_name = result.method.queue

    channel.queue_bind(exchange='eCommerce', queue=queue_name, routing_key='pagamento.aprovado')

    channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=False)
    channel.start_consuming()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)