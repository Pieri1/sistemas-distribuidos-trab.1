// ============================================================================
// 1. COMO CONSUMIR UMA API REST USANDO fetch() (GET e POST)
// ============================================================================
const API_REST_URL = "http://localhost:8000";

async function carregarProdutos() {
    const saida = document.getElementById("saida-rest");
    try {
        // Faz uma requisição HTTP GET para o FastAPI
        const resposta = await fetch(`${API_REST_URL}/produtos`);
        const dados = await resposta.json();
        saida.textContent = JSON.stringify(dados, null, 2);
    } catch (erro) {
        saida.textContent = "❌ Erro ao conectar na porta 8000. O Tutorial 1 está rodando?";
    }
}

async function criarProdutoTeste() {
    const saida = document.getElementById("saida-rest");
    try {
        const novoProduto = {
            nome: "Headset Bluetooth",
            categoria: "A",
            preco: 350.0,
            estoque: 8
        };

        // Faz uma requisição HTTP POST enviando JSON no body
        const resposta = await fetch(`${API_REST_URL}/produtos`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(novoProduto)
        });

        const dados = await resposta.json();
        saida.textContent = JSON.stringify(dados, null, 2);
    } catch (erro) {
        saida.textContent = "❌ Erro ao fazer POST na porta 8000. O Tutorial 1 está rodando?";
    }
}


// ============================================================================
// 2. COMO ESCUTAR NOTIFICAÇÕES EM TEMPO REAL USANDO EventSource (SSE)
// ============================================================================
const API_SSE_URL = "http://localhost:8003";
let eventSource = null;

function conectarSSE() {
    if (eventSource) {
        eventSource.close();
    }

    const badge = document.getElementById("status-sse");
    const lista = document.getElementById("lista-eventos-sse");

    // A classe nativa EventSource abre a conexão persistente com o endpoint SSE do FastAPI!
    eventSource = new EventSource(`${API_SSE_URL}/sse/pedidos`);

    eventSource.onopen = () => {
        badge.textContent = "🟢 Conectado (Aguardando eventos...)";
        lista.innerHTML = "";
    };

    // Toda vez que o servidor FastAPI der `yield "data: {...}\n\n"`, esta função é chamada automaticamente!
    eventSource.onmessage = (event) => {
        const dados = JSON.parse(event.data);
        const item = document.createElement("li");
        const horario = new Date().toLocaleTimeString();

        if (dados.tipo === "conexao") {
            item.innerHTML = `[${horario}] ✅ <strong>${dados.mensagem}</strong>`;
        } else {
            item.innerHTML = `[${horario}] 📦 Pedido <strong>${dados.id_pedido}</strong> mudou para: <strong>${dados.status}</strong>`;
        }
        lista.prepend(item);
    };

    eventSource.onerror = () => {
        badge.textContent = "🔴 Erro / Desconectado (Verifique se o Tutorial 3 está rodando na porta 8003)";
    };
}

async function dispararEventoTeste() {
    const statusPossiveis = ["Estoque Confirmado", "Pagamento Aprovado", "Pedido Enviado"];
    const statusSorteado = statusPossiveis[Math.floor(Math.random() * statusPossiveis.length)];
    await fetch(`${API_SSE_URL}/simular-evento?id_pedido=ped-42&status=${encodeURIComponent(statusSorteado)}`, {
        method: "POST"
    });
}


// ============================================================================
// 3. COMO ABRIR A URL DE PAGAMENTO EM UMA NOVA ABA DO NAVEGADOR
// ============================================================================
function abrirCheckoutMock() {
    // No Trabalho 2, você receberá essa URL como resposta ao criar o pedido / pagamento
    // e usará window.open(url, '_blank') para abrir a tela de decisão em outra aba!
    const urlExemplo = "http://localhost:8002/checkout/pedido-99";
    window.open(urlExemplo, "_blank");
}

