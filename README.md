# Sistema Distribuído de E-Commerce com Microsserviços, REST, RabbitMQ, SSE, Webhooks e Criptografia Assimétrica

## Sobre o Projeto
Este projeto consiste em uma aplicação Web completa de e-commerce baseada em microsserviços desenvolvida para a disciplina de **Sistemas Distribuídos** da **UTFPR**.

O sistema combina:
- **Frontend Web (Node.js / Express + HTML/CSS/JS)**: Interface gráfica desenvolvida em linguagem diferente do backend, consumindo a API REST do Gateway e recebendo atualizações em tempo real via **SSE (Server-Sent Events)**.
- **API Gateway / MS Principal (Python + FastAPI)**: Ponto de entrada REST e gerenciador de conexões SSE, traduzindo ações dos usuários em eventos assinados digitalmente para o **RabbitMQ**.
- **Mensageria com RabbitMQ + Assinatura Digital RSA (2048 bits)**: Comunicação assíncrona entre microsserviços com garantia de autenticidade e integridade via `pycryptodome` (`seguranca.py`).
- **Mock de Pagamento + Webhook**: Sistema externo acionado em nova aba do navegador que processa a aprovação/recusa do pagamento e notifica o **MS Pagamento** via HTTP POST (**Webhook**).
- **Integração com API Externa de E-mail (Resend)**: O **MS Promoções** consome os interesses cadastrados (`interesse.promocao`) e dispara notificações por e-mail via REST.

---

## Arquitetura e Portas dos Serviços

| Componente | Caminho | Porta HTTP | Responsabilidades Principais |
| :--- | :--- | :--- | :--- |
| **Frontend Web** | `frontend/server.js` | `3000` | Catálogo, carrinho, abertura do checkout em nova aba, acompanhamento SSE e cadastro de e-mail para promoções. |
| **MS Principal (API Gateway)** | `ms_principal/main.py` | `8000` | Endpoints REST (`/produtos`, `/pedidos`, `/interesses`), canal SSE (`/sse/pedidos`) e publicação/consumo no RabbitMQ. |
| **MS Estoque** | `ms_estoque/estoque.py` | `8001` | Consome `pedido.criado` e `pedido.excluido`, **persiste o estoque em `data/estoque_produtos.csv`** e expõe `GET /produtos` para o Gateway. |
| **MS Pagamento** | `ms_pagamento/pagamento.py` | `8002` | Consome `pedido.estoque_ok`, solicita cobrança via REST ao Mock e expõe `POST /webhook/pagamento` para publicar `pagamento.aprovado` ou `pagamento.recusado`. |
| **Mock de Pagamento** | `mock_pagamento/mock_pagamento.py` | `8003` | Recebe `POST /cobrancas`, renderiza a página `GET /checkout/{id}` com botões Aprovar/Recusar e dispara o **Webhook** para o MS Pagamento. |
| **MS Entrega** | `ms_entrega/entrega.py` | — | Consome `pagamento.aprovado`, simula emissão de Nota Fiscal e despacho, e publica `pedido.enviado`. |
| **MS Promoções** | `ms_promocoes/promo.py` | — | Consome `interesse.promocao`, gera promoções por categoria e envia e-mails via API externa (**Resend**). |

---

## Pré-requisitos

* **Python 3.10+** e **Node.js 18+**
* Instância do **RabbitMQ** ativa (host `rabbitmq` por padrão, ou defina `export RABBITMQ_HOST=localhost`).
* Instalar dependências do Backend Python:
  ```bash
  pip install -r requirements.txt
  ```
* Instalar dependências do Frontend Node.js:
  ```bash
  cd frontend && npm install
  ```
* *(Opcional)* Para envio real de e-mails pelo **Resend** no `ms_promocoes`:
  ```bash
  export RESEND_API_KEY="re_sua_chave_aqui"
  ```

---

## Como Executar

### Terminal 1 — Todos os Microsserviços Backend (Python)
Na raiz do projeto (`/workspace`), execute:
```bash
python run_servicos.py
```
*(Documentação Swagger UI do API Gateway disponível em: `http://localhost:8000/docs`)*

### Terminal 2 — Frontend Web (Node.js / Express)
Na pasta `frontend/`, execute:
```bash
cd frontend
npm start
```
Acesse a aplicação no navegador em: **`http://localhost:3000`**
