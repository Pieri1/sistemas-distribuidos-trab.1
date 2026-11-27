# Guia de Estudos e Tutoriais Práticos — Trabalho 2 (REST, MOM, SSE e Webhooks)

Esta pasta contém **5 tutoriais práticos e independentes** criados para você aprender cada tecnologia nova exigida em `Trab2_REST_MOM_SSE_2026_2.pdf` antes de integrá-las ao projeto principal.

---

## Mapa dos Tutoriais Criados

| Pasta | O que você vai aprender | Onde será aplicado no Trabalho 2 |
| :--- | :--- | :--- |
| **[`1-rest-basico/`](./1-rest-basico/README.md)** | Criar APIs REST com **FastAPI** (`GET`, `POST`, `DELETE`, `CORS`, Swagger `/docs`) e consumir endpoints em Python com `requests`. | **MS Estoque** (expor `/produtos`) e **API Gateway** (expor rotas para o Frontend e consultar o MS Estoque via `requests.get`). |
| **[`2-webhooks/`](./2-webhooks/README.md)** | Como funciona o padrão **Webhook** (callback HTTP POST) e página de checkout com botões Aprovar/Recusar. | **MS Pagamento** (solicitar cobrança e expor endpoint de Webhook) e **Mock de Pagamento** (sistema externo). |
| **[`3-sse-tempo-real/`](./3-sse-tempo-real/README.md)** | Como criar um canal **SSE (`text/event-stream`)** no FastAPI usando filas (`queue.Queue`) integradas a threads. | **MS Principal / API Gateway** (notificar o Frontend em tempo real quando o RabbitMQ avisar mudanças no pedido). |
| **[`4-frontend-node-express/`](./4-frontend-node-express/README.md)** | Criar um **Frontend Web em Node.js + Express + HTML/JS** usando `fetch()`, `new EventSource()` e `window.open()`. | **Frontend Web** (em linguagem diferente do backend Python). |
| **[`5-email-api-externa/`](./5-email-api-externa/README.md)** | Como consumir uma **API Externa de E-mail (Resend)** via `requests.post` com autenticação Bearer. | **MS Promoções** (enviar e-mails reais para os clientes cadastrados em `interesse.promocao`). |

---

## Ordem Recomendada de Estudo

1. Comece pelo **[`1-rest-basico`](./1-rest-basico/README.md)** e brinque com o Swagger UI em `http://localhost:8000/docs`.
2. Siga para o **[`2-webhooks`](./2-webhooks/README.md)** para ver dois servidores conversando e o clique no navegador disparando um Webhook.
3. Rode o **[`3-sse-tempo-real`](./3-sse-tempo-real/README.md)** para entender como o servidor empurra eventos sem o cliente precisar recarregar a página.
4. Suba o **[`4-frontend-node-express`](./4-frontend-node-express/README.md)** na porta `3000` para ver o JavaScript conversando com os servidores FastAPI via REST e SSE.
5. Por fim, veja o **[`5-email-api-externa`](./5-email-api-externa/README.md)** para entender o disparo de e-mails no MS Promoções.

