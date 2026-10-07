"use client";

import { useEffect, useState } from "react";

const products = [
  { id: 1, name: "Café Origens", category: "Cafés", price: 32.9 },
  { id: 2, name: "Chá Maré Alta", category: "Chás", price: 24.5 },
  { id: 3, name: "Granola da Casa", category: "Cereais", price: 29.9 },
  { id: 4, name: "Biscoito Cacau", category: "Doces", price: 18.9 },
  { id: 5, name: "Azeite Primeiro Sol", category: "Despensa", price: 46.9 },
  { id: 6, name: "Mel Serra Clara", category: "Despensa", price: 21.9 },
];

const formatMoney = (value) => `R$ ${value.toFixed(2).replace(".", ",")}`;

export default function Home() {
  const [screen, setScreen] = useState("catalogo");
  const [category, setCategory] = useState("Todas");
  const [cart, setCart] = useState([]);
  const [orders, setOrders] = useState([
    { id: "OR-2048", status: "Pagamento aprovado", total: 67.4 },
  ]);
  const [sseConnected, setSseConnected] = useState(true);
  const [email, setEmail] = useState("");
  const [selectedInterests, setSelectedInterests] = useState(["Cafés"]);
  const [subscribed, setSubscribed] = useState(false);
  const [message, setMessage] = useState("");

  const filteredProducts = category === "Todas"
    ? products
    : products.filter((product) => product.category === category);
  const cartCount = cart.reduce((total, item) => total + item.quantity, 0);
  const cartTotal = cart.reduce((total, item) => total + item.price * item.quantity, 0);

  useEffect(() => {
    if (!sseConnected) return undefined;
    const timer = window.setTimeout(() => {
      setOrders((current) => current.map((order, index) => index === 0
        ? { ...order, status: "Estoque confirmado" }
        : order));
      setMessage("Nova atualização recebida via SSE.");
    }, 7000);
    return () => window.clearTimeout(timer);
  }, [sseConnected]);

  function addToCart(product) {
    setCart((current) => {
      const existing = current.find((item) => item.id === product.id);
      if (existing) {
        return current.map((item) => item.id === product.id
          ? { ...item, quantity: item.quantity + 1 }
          : item);
      }
      return [...current, { ...product, quantity: 1 }];
    });
    setMessage(`${product.name} adicionado ao carrinho.`);
  }

  function changeQuantity(id, amount) {
    setCart((current) => current
      .map((item) => item.id === id ? { ...item, quantity: item.quantity + amount } : item)
      .filter((item) => item.quantity > 0));
  }

  function checkout() {
    if (!cart.length) return;
    const paymentWindow = window.open("", "_blank");
    if (paymentWindow) {
      paymentWindow.document.write(`<!doctype html><html lang="pt-BR"><head><title>Mock de Pagamento</title></head><body><h1>Mock de Pagamento</h1><p>Pedido OR-2051</p><p>Total: ${formatMoney(cartTotal)}</p><button onclick="window.close()">Aprovar pagamento</button></body></html>`);
      paymentWindow.document.close();
    }
    setOrders((current) => [
      { id: "OR-2051", status: "Pagamento aprovado", total: cartTotal },
      ...current,
    ]);
    setCart([]);
    setMessage("Pedido criado. O pagamento foi aberto em uma nova aba.");
    setScreen("pedidos");
  }

  function toggleInterest(interest) {
    setSelectedInterests((current) => current.includes(interest)
      ? current.filter((item) => item !== interest)
      : [...current, interest]);
  }

  function subscribe(event) {
    event.preventDefault();
    if (email && selectedInterests.length) setSubscribed(true);
  }

  return (
    <main>
      <header>
        <h1>Origens</h1>
        <p>Catálogo e pedidos</p>
      </header>

      <nav aria-label="Telas">
        <button type="button" onClick={() => setScreen("catalogo")}>1. Catálogo</button>
        <button type="button" onClick={() => setScreen("carrinho")}>2. Carrinho ({cartCount})</button>
        <button type="button" onClick={() => setScreen("pedidos")}>3. Pedidos</button>
        <button type="button" onClick={() => setScreen("promocoes")}>4. Promoções</button>
      </nav>

      {message && <p role="status"><strong>{message}</strong> <button type="button" onClick={() => setMessage("")}>Fechar</button></p>}

      {screen === "catalogo" && (
        <section aria-labelledby="catalogo-titulo">
          <h2 id="catalogo-titulo">Tela 1: Catálogo de produtos</h2>
          <label htmlFor="category">Categoria: </label>
          <select id="category" value={category} onChange={(event) => setCategory(event.target.value)}>
            {["Todas", "Cafés", "Chás", "Cereais", "Doces", "Despensa"].map((item) => <option key={item}>{item}</option>)}
          </select>
          <table>
            <thead><tr><th>Produto</th><th>Categoria</th><th>Preço</th><th>Ação</th></tr></thead>
            <tbody>{filteredProducts.map((product) => <tr key={product.id}><td>{product.name}</td><td>{product.category}</td><td>{formatMoney(product.price)}</td><td><button type="button" onClick={() => addToCart(product)}>Adicionar ao carrinho</button></td></tr>)}</tbody>
          </table>
        </section>
      )}

      {screen === "carrinho" && (
        <section aria-labelledby="carrinho-titulo">
          <h2 id="carrinho-titulo">Tela 2: Carrinho e pedido</h2>
          {!cart.length && <p>O carrinho está vazio.</p>}
          {cart.length > 0 && <table><thead><tr><th>Produto</th><th>Quantidade</th><th>Preço</th><th>Subtotal</th></tr></thead><tbody>{cart.map((item) => <tr key={item.id}><td>{item.name}</td><td><button type="button" onClick={() => changeQuantity(item.id, -1)}>-</button> {item.quantity} <button type="button" onClick={() => changeQuantity(item.id, 1)}>+</button></td><td>{formatMoney(item.price)}</td><td>{formatMoney(item.price * item.quantity)}</td></tr>)}</tbody></table>}
          <p><strong>Total: {formatMoney(cartTotal)}</strong></p>
          <button type="button" disabled={!cart.length} onClick={checkout}>Finalizar pedido e abrir pagamento</button>
        </section>
      )}

      {screen === "pedidos" && (
        <section aria-labelledby="pedidos-titulo">
          <h2 id="pedidos-titulo">Tela 3: Acompanhamento de pedidos</h2>
          <p>SSE: <strong>{sseConnected ? "conectado" : "desconectado"}</strong> <button type="button" onClick={() => setSseConnected(!sseConnected)}>{sseConnected ? "Desconectar" : "Conectar"}</button></p>
          <p>As alterações de status aparecem nesta lista em tempo real.</p>
          <table><thead><tr><th>Pedido</th><th>Total</th><th>Status</th></tr></thead><tbody>{orders.map((order) => <tr key={order.id}><td>{order.id}</td><td>{formatMoney(order.total)}</td><td>{order.status}</td></tr>)}</tbody></table>
        </section>
      )}

      {screen === "promocoes" && (
        <section aria-labelledby="promocoes-titulo">
          <h2 id="promocoes-titulo">Tela 4: Inscrição de promoções</h2>
          {subscribed ? <p role="status">Inscrição realizada para {email}.</p> : <form onSubmit={subscribe}>
            <p><label htmlFor="email">E-mail:</label><br /><input id="email" type="email" required value={email} onChange={(event) => setEmail(event.target.value)} /></p>
            <fieldset><legend>Categorias de interesse:</legend>{["Cafés", "Chás", "Despensa", "Doces"].map((interest) => <label key={interest}><input type="checkbox" checked={selectedInterests.includes(interest)} onChange={() => toggleInterest(interest)} /> {interest}<br /></label>)}</fieldset>
            <button type="submit">Cadastrar e-mail</button>
          </form>}
        </section>
      )}
    </main>
  );
}