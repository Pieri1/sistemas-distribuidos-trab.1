import pika
import sys
import json
import csv
from pathlib import Path
from seguranca import assinar_payload, validar_envelope

with open(Path(__file__).parent.parent / "data" / "estoque_produtos.csv", newline="", encoding="utf-8") as arq:
    registros = csv.reader(arq)
    next(registros)
    estoque = {registro[0]: int(registro[4]) for registro in registros}

reservas = {}

def callback(ch, method, properties, body):
    evento = method.routing_key
    mensagem = validar_envelope(body.decode("utf-8"), key_path="public_keys/principal.pem")

    if mensagem is None:
        print(f"\n [❌] Descartado {evento}: Assinatura digital inválida!")
        ch.basic_ack(delivery_tag=method.delivery_tag)
        return

    id_pedido = mensagem.get("id_pedido")
    print(f"\nRecebido e validado {evento}: {mensagem}")

    if evento == "pedido.criado":
        produtos_solicitados = mensagem.get("produtos", {})
        
        dispcheck = True
        for produto, quant in produtos_solicitados.items():
            if estoque.get(produto, 0) < quant:
                dispcheck = False
                break
        
        if dispcheck:
            for produto, quantidade in produtos_solicitados.items():
                estoque[produto] -= quantidade
            
            reservas[id_pedido] = produtos_solicitados
            
            print(f"\nEnviando 'pedido.estoque_ok': {id_pedido}")
            mensagem_json = {"id_pedido": id_pedido}
            payload = assinar_payload(mensagem_json, key_path="private_key.pem")

            ch.basic_publish(
                exchange='eCommerce',
                routing_key='pedido.estoque_ok',
                body=json.dumps(payload)
            )
        else:
            print(f"\n Enviando 'estoque.indisponivel': {id_pedido}")
            mensagem_json = {"id_pedido": id_pedido}
            payload = assinar_payload(mensagem_json, key_path="private_key.pem")
            ch.basic_publish(
                exchange='eCommerce',
                routing_key='estoque.indisponivel',
                body=json.dumps(payload)
            )

    elif evento == "pedido.excluido":
        reservados = reservas.get(id_pedido)
        if reservados:
            for produto, quant in reservados.items():
                estoque[produto] += quant
            del reservas[id_pedido]
            print(f"\nRemovido da reserva: {id_pedido}")
            
    print(f" Estoque: {estoque}")
    ch.basic_ack(delivery_tag=method.delivery_tag)

def main():
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host='rabbitmq'))
    channel = connection.channel()

    channel.exchange_declare(exchange='eCommerce', exchange_type='direct')

    result = channel.queue_declare(queue='fila.estoque', exclusive=False)
    queue_name = result.method.queue

    routing_keys = ['pedido.criado', 'pedido.excluido']
    for rk in routing_keys:
        channel.queue_bind(exchange='eCommerce', queue=queue_name, routing_key=rk)

    print(f" Estoque: {estoque}")

    channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=False)
    channel.start_consuming()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)