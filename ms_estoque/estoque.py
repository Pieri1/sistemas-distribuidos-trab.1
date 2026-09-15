import pika
import sys
import json
import csv
from pathlib import Path

with open(Path(__file__).parent.parent / "data" / "estoque_produtos.csv", newline="", encoding="utf-8") as arq:
    registros = csv.reader(arq)
    next(registros)
    estoque = {registro[0]: int(registro[4]) for registro in registros}

reservas = {}

def callback(ch, method, properties, body):
    evento = method.routing_key
    mensagem = json.loads(body)
    id_pedido = mensagem.get("id_pedido")
    
    print(f"\nRecebido {evento}: {mensagem}")

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
            ch.basic_publish(
                exchange='eCommerce',
                routing_key='pedido.estoque_ok',
                body=json.dumps({"id_pedido": id_pedido})
            )
        else:
            print(f"\n Enviando 'estoque.indisponivel': {id_pedido}")
            ch.basic_publish(
                exchange='eCommerce',
                routing_key='estoque.indisponivel',
                body=json.dumps({"id_pedido": id_pedido})
            )

    elif evento == "pedido.excluido":
        reservados = reservas.get(id_pedido)
        if reservados:
            for produto, quant in reservados.items():
                estoque[produto] += quant
            del reservas[id_pedido]
            print(f"\nRemovido da reserva: {id_pedido}")
            
    print(f" Estoque: {estoque}")

def main():
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host='rabbitmq'))
    channel = connection.channel()

    channel.exchange_declare(exchange='eCommerce', exchange_type='direct')

    result = channel.queue_declare(queue='fila_estoque', exclusive=False)
    queue_name = result.method.queue

    routing_keys = ['pedido.criado', 'pedido.excluido']
    for rk in routing_keys:
        channel.queue_bind(exchange='eCommerce', queue=queue_name, routing_key=rk)

    print(f" Estoque: {estoque}")

    channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)
    channel.start_consuming()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)