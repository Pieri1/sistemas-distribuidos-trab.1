import pika
import sys
import json
import threading
import uuid
import csv
from pathlib import Path

pedidos = {}
with open(Path(__file__).parent.parent / "data" / "estoque_produtos.csv", newline="", encoding="utf-8") as arq:
    registros = csv.reader(arq)
    next(registros)
    catalogo_produtos = {registro[0]: float(registro[3]) for registro in registros}

def publish(routing_key, mensagem):
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host='rabbitmq'))
    channel = connection.channel()

    channel.exchange_declare(exchange='eCommerce', exchange_type='direct')

    channel.basic_publish(
        exchange='eCommerce',
        routing_key=routing_key,
        body=json.dumps(mensagem)
    )
    connection.close()

def callback_consumidor(ch, method, properties, body):
    evento = method.routing_key
    mensagem = json.loads(body)
    id_pedido = mensagem.get("id_pedido")
    
    if id_pedido in pedidos:
        pedidos[id_pedido]['status'] = evento
        print(f"\nPedido {id_pedido} atualizado para: {evento}")

        if evento in ["estoque.indisponivel", "pagamento.recusado"]:
            print(f"\nEnviando 'pedido.excluido': {id_pedido}...")
            ch.basic_publish(
                exchange='eCommerce',
                routing_key='pedido.excluido',
                body=json.dumps({"id_pedido": id_pedido})
            )
            pedidos[id_pedido]['status'] = "pedido.excluido"
            
    print("\nComando (1-Visualizar, 2-Comprar, 3-Excluir, 4-Status, 5-Sair): ", end="")

def iniciar_consumidor():
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host='rabbitmq'))
    channel = connection.channel()

    result = channel.queue_declare(queue='fila_principal', exclusive=False)
    queue_name = result.method.queue

    routing_keys = [
        'pagamento.aprovado', 'pagamento.recusado', 
        'pedido.enviado', 'pedido.estoque_ok', 'estoque.indisponivel'
    ]
    for rk in routing_keys:
        channel.queue_bind(exchange='eCommerce', queue=queue_name, routing_key=rk)

    channel.basic_consume(queue=queue_name, on_message_callback=callback_consumidor, auto_ack=True)
    channel.start_consuming()

def main():
    while True:
        try:
            print("\n--- Selecione sua opção ---")
            print("1. Visualizar produtos")
            print("2. Realizar pedido")
            print("3. Excluir pedido")
            print("4. Consultar meus pedidos")
            print("5. Sair")
            opcao = input("Escolha uma opção: ")

            if opcao == '1':
                print("\n--- Produtos ---")
                for p, preco in catalogo_produtos.items():
                    print(f"- {p}: R$ {preco:.2f}")

            elif opcao == '2':
                produto = input("Digite o id do produto: ")
                qtd = int(input("Quantidade: "))
                
                id_pedido = str(uuid.uuid4())[:8]
                pedidos[id_pedido] = {
                    "produtos": {produto: qtd},
                    "status": "pedido.criado"
                }
                
                mensagem = {"id_pedido": id_pedido, "produtos": {produto: qtd}}
                publish('pedido.criado', mensagem)
                print(f"\nEnviando 'pedido.criado': {id_pedido}")

            elif opcao == '3':
                id_pedido = input("Digite o ID do pedido: ")
                if id_pedido in pedidos:
                    publish('pedido.excluido', {"id_pedido": id_pedido})
                    pedidos[id_pedido]['status'] = "pedido.excluido (manual)"
                    print(f"\nEnviando 'pedido.excluido': {id_pedido}")
                else:
                    print("\nPedido não encontrado")

            elif opcao == '4':
                print("\n--- Meus Pediso ---")
                for pid, info in pedidos.items():
                    print(f"ID: {pid} | Produtos: {info['produtos']} | Status: {info['status']}")

            elif opcao == '5':
                print("Encerrando...")
                sys.exit(0)
            else:
                print("Opção inválida!")
        except Exception as e:
            print(f"Erro: {e}")

if __name__ == '__main__':
    thread_consumidor = threading.Thread(target=iniciar_consumidor, daemon=True)
    thread_consumidor.start()

    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)