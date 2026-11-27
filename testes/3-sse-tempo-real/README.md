# Tutorial 3: Server-Sent Events (SSE) em Tempo Real com FastAPI

## O que é SSE (Server-Sent Events)?
Diferente de uma requisição REST comum (onde o navegador pede um dado e a conexão fecha logo em seguida), no **SSE** o navegador abre uma conexão HTTP do tipo `text/event-stream` e **mantém essa conexão aberta**.
Sempre que o servidor tiver uma novidade (ex: o RabbitMQ avisou que o estoque foi confirmado ou que o pagamento foi aprovado), o servidor escreve uma linha no formato:
```text
data: {"id_pedido": "123", "status": "pedido.estoque_ok"}

```
*(Repare nas duas quebras de linha `\n\n` ao final — isso é obrigatório no protocolo SSE para indicar o fim de uma mensagem!)*

---

## Onde você vai usar isso no Trabalho 2?
No **MS Principal (API Gateway)** (vale **0,5 ponto** da nota!):
- O Frontend abre uma conexão SSE em `GET /eventos-pedidos`.
- O `ms_principal` já tem uma `threading.Thread` escutando o RabbitMQ (`pedido.estoque_ok`, `pagamento.aprovado`, `pagamento.recusado`, `pedido.enviado`).
- Toda vez que o `callback_consumidor` do RabbitMQ receber um evento, ele coloca esse evento na fila dos clientes SSE conectados, e o navegador recebe na mesma hora!

---

## Como Executar e Testar este Tutorial

### Passo 1: Iniciar o Servidor SSE (Terminal 1)
Na pasta `testes/3-sse-tempo-real`, execute:
```bash
uvicorn servidor_sse:app --reload --port 8003
```

### Passo 2: Escutar o Stream SSE em Tempo Real (Terminal 2 ou Navegador)
Abra um segundo terminal e rode o comando `curl -N` (o `-N` desativa o buffer para mostrar na hora):
```bash
curl -N http://localhost:8003/sse/pedidos
```
*(Ou use o Frontend Node.js do **Tutorial 4**, que se conecta visualmente a este servidor!)*

### Passo 3: Simular Eventos Chegando do RabbitMQ
Com o `curl` aberto esperando eventos, abra `http://localhost:8003/docs` no navegador (ou um 3º terminal) e chame a rota `POST /simular-evento`:
```bash
curl -X POST "http://localhost:8003/simular-evento?id_pedido=ped-01&status=Estoque%20Confirmado"
```
Você verá a notificação aparecer **instantaneamente** na janela que está escutando o `/sse/pedidos`!

