from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# 1. Inicializa a aplicação FastAPI
# A documentação interativa (Swagger UI) fica disponível automaticamente em: http://localhost:8000/docs
app = FastAPI(title="Tutorial 1 - API REST Básica")

# 2. Configuração de CORS (Cross-Origin Resource Sharing)
# MUITO IMPORTANTE: Como o seu Frontend (Node.js/Express) vai rodar em uma porta diferente
# (ex: porta 3000) da porta do Backend (ex: porta 8000), o navegador bloquearia as requisições
# se não habilitarmos o CORS abaixo.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permite chamadas de qualquer origem (ex: localhost:3000)
    allow_credentials=True,
    allow_methods=["*"],  # Permite GET, POST, DELETE, PUT, etc.
    allow_headers=["*"],
)


# 3. Modelos de Dados (Pydantic)
# O FastAPI usa classes BaseModel para validar automaticamente o JSON recebido no body de um POST!
class NovoProduto(BaseModel):
    nome: str
    categoria: str
    preco: float
    estoque: int


# Simulando um banco de dados em memória (no projeto real, vem do CSV no MS Estoque)
banco_produtos = {
    "1": {"nome": "Teclado Mecânico", "categoria": "A", "preco": 250.0, "estoque": 10},
    "2": {"nome": "Mouse Gamer", "categoria": "B", "preco": 120.0, "estoque": 5},
}


# ==========================================
# ROTAS / ENDPOINTS DA API
# ==========================================

# [GET] Listar todos os produtos
@app.get("/produtos")
def listar_produtos():
    """Retorna todos os produtos cadastrados."""
    return {"produtos": banco_produtos}


# [GET] Buscar um produto específico por ID (parâmetro na URL)
@app.get("/produtos/{id_produto}")
def obter_produto(id_produto: str):
    """Busca um único produto pelo seu ID."""
    if id_produto not in banco_produtos:
        # Retorna erro HTTP 404 caso não exista
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    return banco_produtos[id_produto]


# [POST] Criar um novo recurso enviando JSON no corpo (body) da requisição
@app.post("/produtos", status_code=201)
def criar_produto(produto: NovoProduto):
    """Cria um novo produto a partir do JSON enviado pelo cliente."""
    novo_id = str(len(banco_produtos) + 1)
    # .model_dump() converte o objeto Pydantic para dicionário Python
    banco_produtos[novo_id] = produto.model_dump()
    return {
        "mensagem": "Produto criado com sucesso!",
        "id": novo_id,
        "dados": banco_produtos[novo_id],
    }


# [DELETE] Remover um recurso (no Trabalho 2 será útil para cancelar interesse de promoção!)
@app.delete("/produtos/{id_produto}")
def deletar_produto(id_produto: str):
    """Remove um produto pelo ID."""
    if id_produto not in banco_produtos:
        raise HTTPException(status_code=404, detail="Produto não encontrado")

    removido = banco_produtos.pop(id_produto)
    return {"mensagem": f"Produto {id_produto} removido!", "removido": removido}

