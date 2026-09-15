import pika
import sys
import json
import threading
import uuid
import csv
from pathlib import Path
from seguranca import assinar_payload, validar_envelope

ORIGEM_CHAVES = {
    "pedido.estoque_ok": "public_keys/estoque.pem",
    "estoque.indisponivel": "public_keys/estoque.pem",
    "pagamento.aprovado": "public_keys/pagamento.pem",
    "pagamento.recusado": "public_keys/pagamento.pem",
    "pedido.enviado": "public_keys/entrega.pem",
}

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
    payload = assinar_payload(mensagem, key_path="private_key.pem")

    channel.basic_publish(
        exchange='eCommerce',
        routing_key=routing_key,
        body=json.dumps(payload)
    )
    connection.close()

def callback_consumidor(ch, method, properties, body):
    evento = method.routing_key
    key = ORIGEM_CHAVES.get(evento)
    mensagem = validar_envelope(body.decode("utf-8"), key_path=key)

    if mensagem is None:
        print(f"\n [❌] Descartado {evento}: Assinatura digital inválida!")
        ch.basic_ack(delivery_tag=method.delivery_tag)
        return

    id_pedido = mensagem.get("id_pedido")
    
    if id_pedido in pedidos:
        pedidos[id_pedido]['status'] = evento
        print(f"\nPedido {id_pedido} atualizado para: {evento}")

        if evento in ["estoque.indisponivel", "pagamento.recusado"]:
            print(f"\nEnviando 'pedido.excluido': {id_pedido}...")
            mensagem_json = {"id_pedido": id_pedido}
            payload = assinar_payload(mensagem_json, key_path="private_key.pem")
            ch.basic_publish(
                exchange='eCommerce',
                routing_key='pedido.excluido',
                body=json.dumps(payload)
            )
            pedidos[id_pedido]['status'] = "pedido.excluido"
            
    print("\nComando (1-Visualizar, 2-Comprar, 3-Excluir, 4-Status, 5-Sair): ", end="")
    ch.basic_ack(delivery_tag=method.delivery_tag)

def iniciar_consumidor():
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host='rabbitmq'))
    channel = connection.channel()

    result = channel.queue_declare(queue='fila_principal', exclusive=False)
    queue_name = result.method.queue

    for rk in ORIGEM_CHAVES.keys():
        channel.queue_bind(exchange='eCommerce', queue=queue_name, routing_key=rk)

    channel.basic_consume(queue=queue_name, on_message_callback=callback_consumidor, auto_ack=False)
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
                produtos = {}
                while True:
                    produto = input("Digite o id do produto (0 para sair): ")
                    if produto == "0":
                        break
                    produtos[produto] = int(input("Quantidade: "))

                if not produtos:
                    continue
                
                id_pedido = str(uuid.uuid4())[:8]
                pedidos[id_pedido] = {
                    "produtos": produtos,
                    "status": "pedido.criado"
                }
                
                mensagem = {"id_pedido": id_pedido, "produtos": produtos}
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
                print("\n--- Meus Pedidos ---")
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