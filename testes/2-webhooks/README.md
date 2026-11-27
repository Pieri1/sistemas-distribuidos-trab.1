# Tutorial 2: Padrão Webhook (Simulando MS Pagamento + Mock de Pagamento)

## O que é um Webhook?
Em uma chamada REST comum, o Cliente pergunta algo ao Servidor e fica esperando a resposta na mesma hora.
Porém, num pagamento real (ou no **Mock de Pagamento** do Trabalho 2), o usuário demora alguns segundos ou minutos para abrir a página do banco e clicar em **"Pagar"** ou **"Cancelar"**.

Em vez de o **MS Pagamento** ficar perguntando a cada 1 segundo *"E aí, já pagou?"* (polling), usamos um **Webhook** (*"Não me ligue, eu te ligo quando terminar"*):
1. O **MS Pagamento** envia um `POST /cobrancas` para o **Mock de Pagamento**, informando o `id_pedido`, o `valor` e uma **`webhook_url`** (ex: `http://localhost:8001/webhook/pagamento`).
2. O **Mock de Pagamento** devolve imediatamente uma **`checkout_url`** (ex: `http://localhost:8002/checkout/ped-123`).
3. O usuário abre essa **`checkout_url`** em uma nova aba do navegador e clica no botão **"Pagamento Aprovado"** ou **"Pagamento Recusado"**.
4. Quando o usuário clica, o **Mock de Pagamento** faz um `requests.post(webhook_url, json={...})` avisando o **MS Pagamento** do resultado!

---

## Como Executar este Tutorial

Você vai precisar de **2 terminais** abertos na pasta `testes/2-webhooks`:

### Terminal 1: Iniciar o Mock de Pagamento (Porta 8002)
```bash
uvicorn mock_pagamento_server:app --reload --port 8002
```

### Terminal 2: Iniciar o Serviço de Pagamento que recebe o Webhook (Porta 8001)
```bash
uvicorn meu_servico_webhook:app --reload --port 8001
```

### Passo a Passo para Testar
1. Acesse o Swagger do **Meu Serviço de Pagamento** em `http://localhost:8001/docs` (ou chame via terminal: `curl -X POST http://localhost:8001/iniciar-pagamento/pedido-99`).
2. Execute a rota `POST /iniciar-pagamento/{id_pedido}`.
3. Veja a resposta JSON: ela trará um campo `"checkout_url"` (ex: `http://localhost:8002/checkout/pedido-99`).
4. Abra essa URL no seu navegador! Você verá a telinha com os botões **"Pagamento Aprovado"** e **"Pagamento Recusado"**.
5. Clique em um dos botões e olhe o **Terminal 2** (`meu_servico_webhook`): ele receberá instantaneamente a chamada de Webhook com o status escolhido!

