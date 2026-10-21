const API_GATEWAY_URL = "http://localhost:8000";

let catalogoProdutos = [];
let carrinho = {};
let pedidosLocais = {};

// ============================================================================
// 1. CATÁLOGO DE PRODUTOS (VIA REST GET /produtos NO API GATEWAY)
// ============================================================================
async function carregarProdutos() {
    const container = document.getElementById("lista-produtos");
    try {
        const resp = await fetch(`${API_GATEWAY_URL}/produtos`);
        if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
        const data = await resp.json();
        catalogoProdutos = data.produtos || [];
        renderizarCatalogo();
    } catch (err) {
        container.innerHTML = `<p class="muted">❌ Erro ao buscar produtos no API Gateway (${API_GATEWAY_URL}): ${err.message}</p>`;
    }
}

function renderizarCatalogo() {
    const container = document.getElementById("lista-produtos");
    const filtroCat = document.getElementById("filtro-categoria").value;

    const filtrados = catalogoProdutos.filter(p =>
        filtroCat === "TODAS" || p.cod_categoria === filtroCat
    );

    if (filtrados.length === 0) {
        container.innerHTML = `<p class="muted">Nenhum produto disponível para este filtro.</p>`;
        return;
    }

    container.innerHTML = filtrados.map(p => `
        <div class="product-card">
            <div class="product-info">
                <strong>#${p.cod_produto} — ${p.nom_produto}</strong>
                <div class="product-meta">
                    Categoria: <b>${p.cod_categoria}</b> |
                    Preço: <b>R$ ${Number(p.vlr_produto).toFixed(2)}</b> |
                    Estoque: <b>${p.qtd_estoque} un.</b>
                </div>
            </div>
            <div class="product-actions">
                <input type="number" id="qtd-${p.cod_produto}" min="1" max="${p.qtd_estoque}" value="1" />
                <button class="btn btn-primary btn-sm" onclick="adicionarAoCarrinho('${p.cod_produto}')">
                    + Adicionar
                </button>
            </div>
        </div>
    `).join("");
}

// ============================================================================
// 2. CARRINHO E CRIAÇÃO DE PEDIDOS (VIA REST POST /pedidos)
// ============================================================================
function adicionarAoCarrinho(codProduto) {
    const input = document.getElementById(`qtd-${codProduto}`);
    const qtd = parseInt(input ? input.value : 1, 10);
    if (!qtd || qtd <= 0) return;

    const produtoInfo = catalogoProdutos.find(p => String(p.cod_produto) === String(codProduto));
    if (!produtoInfo) return;

    const atual = carrinho[codProduto] ? carrinho[codProduto].quantidade : 0;
    carrinho[codProduto] = {
        produto: produtoInfo,
        quantidade: atual + qtd
    };
    renderizarCarrinho();
}

function removerDoCarrinho(codProduto) {
    delete carrinho[codProduto];
    renderizarCarrinho();
}

function renderizarCarrinho() {
    const container = document.getElementById("itens-carrinho");
    const totalEl = document.getElementById("valor-total-carrinho");
    const btnFinalizar = document.getElementById("btn-finalizar");

    const chaves = Object.keys(carrinho);
    if (chaves.length === 0) {
        container.innerHTML = `<p class="muted">Seu carrinho está vazio.</p>`;
        totalEl.textContent = "R$ 0,00";
        btnFinalizar.disabled = true;
        return;
    }

    let soma = 0;
    container.innerHTML = chaves.map(cod => {
        const item = carrinho[cod];
        const subtotal = item.produto.vlr_produto * item.quantidade;
        soma += subtotal;
        return `
            <div class="cart-row">
                <span><b>${item.quantidade}x</b> ${item.produto.nom_produto} (#${cod})</span>
                <span>
                    R$ ${subtotal.toFixed(2)}
                    <button class="btn btn-danger btn-sm" onclick="removerDoCarrinho('${cod}')">✕</button>
                </span>
            </div>
        `;
    }).join("");

    totalEl.textContent = `R$ ${soma.toFixed(2)}`;
    btnFinalizar.disabled = false;
}

async function finalizarPedido() {
    const payloadProdutos = {};
    for (const [cod, item] of Object.entries(carrinho)) {
        payloadProdutos[cod] = item.quantidade;
    }

    try {
        const resp = await fetch(`${API_GATEWAY_URL}/pedidos`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ produtos: payloadProdutos })
        });
        if (!resp.ok) throw new Error(`Falha ao criar pedido (${resp.status})`);
        const data = await resp.json();

        carrinho = {};
        renderizarCarrinho();

        pedidosLocais[data.id_pedido] = data.pedido;
        renderizarPedidos();

        // Requisito do PDF: "Pagamento: ao finalizar o pedido, recebe a URL do Mock de Pagamento
        // e abre uma nova aba no navegador para simular o pagamento."
        if (data.checkout_url) {
            window.open(data.checkout_url, "_blank");
        }
    } catch (err) {
        alert(`Erro ao criar pedido: ${err.message}`);
    }
}

async function carregarPedidosExistentes() {
    try {
        const resp = await fetch(`${API_GATEWAY_URL}/pedidos`);
        if (!resp.ok) return;
        const data = await resp.json();
        pedidosLocais = data.pedidos || {};
        renderizarPedidos();
    } catch (_) {}
}

async function excluirPedido(idPedido) {
    try {
        await fetch(`${API_GATEWAY_URL}/pedidos/${idPedido}`, { method: "DELETE" });
        await carregarProdutos();
    } catch (err) {
        alert(`Erro ao excluir pedido: ${err.message}`);
    }
}

function classeBadgeStatus(evento) {
    if (evento === "pedido.enviado" || evento === "pagamento.aprovado" || evento === "pedido.estoque_ok") {
        return "badge-success";
    }
    if (evento === "estoque.indisponivel" || evento === "pagamento.recusado" || evento === "pedido.excluido") {
        return "badge-error";
    }
    return "badge-status";
}

function renderizarPedidos() {
    const container = document.getElementById("lista-pedidos");
    const lista = Object.values(pedidosLocais).reverse();

    if (lista.length === 0) {
        container.innerHTML = `<p class="muted">Nenhum pedido realizado ainda.</p>`;
        return;
    }

    container.innerHTML = lista.map(p => {
        const itensStr = Object.entries(p.produtos || {})
            .map(([cod, qtd]) => `Prod #${cod} (${qtd} un.)`)
            .join(", ");
        const podePagar = p.status === "pedido.estoque_ok" || p.status === "pedido.criado";
        const podeCancelar = p.status !== "pedido.excluido" && p.status !== "pedido.enviado";

        return `
            <div class="order-card">
                <div class="order-header">
                    <strong>Pedido #${p.id_pedido}</strong>
                    <span class="badge ${classeBadgeStatus(p.status)}">${p.status_descricao || p.status}</span>
                </div>
                <div class="product-meta">Itens: ${itensStr}</div>
                <div class="order-actions">
                    ${podePagar ? `<button class="btn btn-primary btn-sm" onclick="window.open('${p.checkout_url}', '_blank')">💳 Abrir Mock de Pagamento</button>` : ""}
                    ${podeCancelar ? `<button class="btn btn-danger btn-sm" onclick="excluirPedido('${p.id_pedido}')">🗑️ Cancelar Pedido</button>` : ""}
                </div>
            </div>
        `;
    }).join("");
}

// ============================================================================
// 3. CONEXÃO SSE (SERVER-SENT EVENTS) COM O API GATEWAY
// ============================================================================
function iniciarConexaoSSE() {
    const badge = document.getElementById("sse-badge");
    const feed = document.getElementById("feed-sse");

    const evtSource = new EventSource(`${API_GATEWAY_URL}/sse/pedidos`);

    evtSource.onopen = () => {
        badge.textContent = "Conectado (Tempo Real)";
        badge.className = "badge badge-connected";
    };

    evtSource.onmessage = (event) => {
        const dados = JSON.parse(event.data);
        const hora = new Date().toLocaleTimeString();

        const li = document.createElement("li");
        if (dados.tipo === "conexao") {
            li.textContent = `[${hora}] ✅ ${dados.mensagem}`;
        } else if (dados.tipo === "atualizacao_pedido") {
            li.textContent = `[${hora}] 📦 Pedido #${dados.id_pedido} -> ${dados.status_descricao} (${dados.evento})`;
            pedidosLocais[dados.id_pedido] = dados.pedido;
            renderizarPedidos();
            carregarProdutos();
        }
        feed.prepend(li);
    };

    evtSource.onerror = () => {
        badge.textContent = "Reconectando...";
        badge.className = "badge badge-disconnected";
    };
}

// ============================================================================
// 4. INSCRIÇÃO E CANCELAMENTO DE PROMOÇÕES (REST POST E DELETE /interesses)
// ============================================================================
function obterCategoriasSelecionadas() {
    const checks = document.querySelectorAll(".cat-check:checked");
    return Array.from(checks).map(c => c.value);
}

async function registrarInteresse() {
    const email = document.getElementById("email-promo").value.trim();
    const categorias = obterCategoriasSelecionadas();
    const feedback = document.getElementById("feedback-promo");

    if (!email || categorias.length === 0) {
        feedback.style.color = "#dc2626";
        feedback.textContent = "Preencha seu e-mail e selecione ao menos uma categoria.";
        return;
    }

    try {
        const resp = await fetch(`${API_GATEWAY_URL}/interesses`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email, categorias })
        });
        const data = await resp.json();
        if (!resp.ok) throw new Error(data.detail || "Erro ao registrar interesse");

        feedback.style.color = "#166534";
        feedback.textContent = `✅ ${data.mensagem}`;
    } catch (err) {
        feedback.style.color = "#dc2626";
        feedback.textContent = `❌ ${err.message}`;
    }
}

async function cancelarInteresse() {
    const email = document.getElementById("email-promo").value.trim();
    const categorias = obterCategoriasSelecionadas();
    const feedback = document.getElementById("feedback-promo");

    if (!email) {
        feedback.style.color = "#dc2626";
        feedback.textContent = "Informe o e-mail para cancelar o recebimento de promoções.";
        return;
    }

    try {
        const resp = await fetch(`${API_GATEWAY_URL}/interesses`, {
            method: "DELETE",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email, categorias })
        });
        const data = await resp.json();
        if (!resp.ok) throw new Error(data.detail || "Erro ao cancelar interesse");

        feedback.style.color = "#0369a1";
        feedback.textContent = `🔕 ${data.mensagem}`;
    } catch (err) {
        feedback.style.color = "#dc2626";
        feedback.textContent = `❌ ${err.message}`;
    }
}

// Inicialização ao abrir a página
window.addEventListener("DOMContentLoaded", () => {
    carregarProdutos();
    carregarPedidosExistentes();
    iniciarConexaoSSE();
});

