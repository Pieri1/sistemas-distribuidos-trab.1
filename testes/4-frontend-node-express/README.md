# Tutorial 4: Frontend Web em Node.js (Express + HTML/JS) Consumindo REST e SSE

## Por que Node.js + Express + HTML/JS?
O enunciado do Trabalho 2 exige:
> *"Frontend web: interface gráfica desenvolvida em **linguagem diferente do backend**. O frontend comunicará com o backend via REST."*

Como o seu Backend é em **Python (FastAPI)**, usar **JavaScript (Node.js/Express + HTML/JS)** cumpre 100% esse requisito de forma limpa e direta!

Neste tutorial você aprenderá os 3 pilares que o seu Frontend precisará ter no Trabalho 2:
1. **`fetch()` (REST)**: Fazer chamadas `GET`, `POST` e `DELETE` para o Backend FastAPI (consultar produtos, criar pedidos, cadastrar e-mail em promoções).
2. **`new EventSource()` (SSE)**: Escutar notificações em tempo real vindas do Backend FastAPI sem precisar recarregar a página.
3. **`window.open(url, '_blank')`**: Abrir a URL do **Mock de Pagamento** automaticamente em uma nova aba do navegador!

---

## Como Executar este Tutorial

### Passo 1: Instalar o Express no Node.js
Na pasta `testes/4-frontend-node-express`, instale as dependências:
```bash
npm install
```

### Passo 2: Iniciar o Servidor Frontend Node.js (Porta 3000)
```bash
npm start
```
Abra no navegador: `http://localhost:3000`

### Passo 3: Testar Integrado com os Tutoriais 1, 2 e 3!
Para ver a página funcionando de ponta a ponta com os tutoriais anteriores:
- Deixe o **Tutorial 1** rodando na porta `8000` (`uvicorn servidor_api:app --port 8000`) -> para testar os botões de **REST (`GET`/`POST`)**.
- Deixe o **Tutorial 3** rodando na porta `8003` (`uvicorn servidor_sse:app --port 8003`) -> para testar o painel de **Notificações em Tempo Real (SSE)**.
- Deixe o **Tutorial 2** rodando nas portas `8001` e `8002` -> para testar o botão de **Abrir Checkout de Pagamento em Nova Aba**!

