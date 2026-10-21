import requests

# URL base onde o servidor_api.py está rodando
URL_BASE = "http://localhost:8000"


def testar_consumo_api():
    print("=== 1. Testando GET /produtos ===")
    # No Trabalho 2, o API Gateway fará exatamente isso para consultar o MS Estoque!
    resposta = requests.get(f"{URL_BASE}/produtos")
    print(f"Status HTTP: {resposta.status_code}")
    print(f"JSON recebido: {resposta.json()}\n")

    print("=== 2. Testando POST /produtos ===")
    novo_item = {
        "nome": "Monitor 24 Pol",
        "categoria": "A",
        "preco": 899.90,
        "estoque": 15,
    }
    # O parâmetro json=... serializa automaticamente o dicionário e adiciona o header Content-Type: application/json
    resposta_post = requests.post(f"{URL_BASE}/produtos", json=novo_item)
    print(f"Status HTTP: {resposta_post.status_code}")
    print(f"JSON recebido: {resposta_post.json()}\n")

    print("=== 3. Testando DELETE /produtos/1 ===")
    resposta_del = requests.delete(f"{URL_BASE}/produtos/1")
    print(f"Status HTTP: {resposta_del.status_code}")
    print(f"JSON recebido: {resposta_del.json()}\n")

    print("=== 4. Conferindo lista atualizada (GET /produtos) ===")
    resposta_final = requests.get(f"{URL_BASE}/produtos")
    print(f"JSON recebido: {resposta_final.json()}")


if __name__ == "__main__":
    try:
        testar_consumo_api()
    except requests.exceptions.ConnectionError:
        print("❌ Erro: Não foi possível conectar ao servidor.")
        print("Certifique-se de rodar antes: uvicorn servidor_api:app --reload --port 8000")

