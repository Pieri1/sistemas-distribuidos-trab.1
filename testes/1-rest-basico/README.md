# Tutorial 1: API REST Básica com FastAPI e Consumo com `requests`

Este tutorial ensina dois conceitos fundamentais para o **Trabalho 2**:
1. **Como criar um servidor REST com FastAPI** (`GET`, `POST`, `DELETE`, validação com `Pydantic` e `CORS`).
2. **Como fazer um microsserviço Python chamar outro via HTTP** usando a biblioteca `requests`.

---

## Onde você vai usar isso no Trabalho 2?
- **MS Estoque**: Precisa expor um endpoint `GET /produtos` para que o API Gateway consulte os produtos disponíveis.
- **MS Principal (API Gateway)**:
  - Expõe endpoints REST para o Frontend (`GET /produtos`, `POST /pedidos`, `POST /interesses`, `DELETE /interesses`).
  - Faz uma chamada HTTP `GET` (usando `requests`) para buscar a lista de produtos diretamente no **MS Estoque**.

---

## Pré-requisitos
Instale o FastAPI, o servidor Uvicorn e a biblioteca `requests`:
```bash
pip install fastapi uvicorn requests
```

---

## Como Executar o Tutorial

### Passo 1: Iniciar o Servidor FastAPI (Terminal 1)
A partir desta pasta (`testes/1-rest-basico`), execute:
```bash
uvicorn servidor_api:app --reload --port 8000
```

### Passo 2: Testar pelo Swagger UI (Navegador)
O FastAPI gera documentação interativa automaticamente! Abra no navegador:
- **Swagger UI**: `http://localhost:8000/docs`
Lá você pode clicar em cada rota (`GET`, `POST`, `DELETE`), clicar em **"Try it out"** e testar sem precisar escrever código.

### Passo 3: Testar o Cliente Python (Terminal 2)
Com o servidor rodando no Terminal 1, abra outro terminal nesta mesma pasta e execute:
```bash
python cliente_python.py
```
Você verá o script Python consultando, criando e removendo produtos no servidor via HTTP REST!

