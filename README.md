# Sistema Distribuído de E-Commerce com RabbitMQ e Criptografia Assimétrica

## Sobre o Projeto
Este projeto consiste no backend de um sistema distribuído de e-commerce orientado a eventos (Event-Driven Architecture) desenvolvido para a disciplina de Sistemas Distribuídos da UTFPR. 

A comunicação entre processos é totalmente desacoplada e realizada exclusivamente por meio do message broker **RabbitMQ**, sem chamadas diretas entre serviços. Além disso, o sistema conta com uma camada de segurança por **criptografia de chave assimétrica (RSA 2048 bits com PKCS#1 v1.5 e SHA-256)**, garantindo autenticidade e integridade através da assinatura e validação digital de todos os eventos transmitidos.

---

## O que foi Feito

* **Arquitetura de Mensageria (RabbitMQ)**:
  * **Exchange `eCommerce` (tipo Direct)**: Gerencia o fluxo transacional de pedidos, estoque, pagamentos e entregas utilizando routing keys hierárquicas e filas exclusivas por serviço.
  * **Exchange `Promoções` (tipo Topic)**: Publica ofertas categorizadas (`promocao.categoria.A`, `promocao.categoria.B`, `promocao.categoria.C`), permitindo que consumidores filtrem eventos via padrões de binding.
* **Microsserviços Implementados**:
  * **MS Principal**: Interface de terminal para interação com o usuário (visualizar produtos, criar/consultar/excluir pedidos).
  * **MS Estoque**: Gerenciamento de disponibilidade, reserva/baixa de produtos e reposição em caso de cancelamento.
  * **MS Pagamento**: Simulação de aprovação/recusa financeira por processamento aleatório.
  * **MS Entrega**: Emissão de notas e preparação do envio dos produtos pós-pagamento.
  * **MS Promoções**: Geração e difusão periódica de descontos por categoria de produto.
* **Consumidores de Notificações**:
  * **Consumidor C1**: Registra interesse e escuta as categorias A e B.
  * **Consumidor C2**: Registra interesse global em todas as promoções.
* **Segurança e Criptografia Assimétrica**:
  * Implementação centralizada (`seguranca.py`) utilizando `pycryptodome`.
  * Cada evento publicado recebe uma assinatura gerada pela chave privada do produtor.
  * Cada consumidor valida a assinatura através da chave pública do remetente antes de processar qualquer mensagem, descartando payloads inválidos ou corrompidos.

---

## Pré-requisitos

* **Python 3.10+**
* Instância do **RabbitMQ** ativa e acessível (host `rabbitmq` ou `localhost` conforme configurado).
* Dependências Python instaladas:

  pip install pika pycryptodome

---

## Como Executar

Com o broker RabbitMQ ativo e a partir do diretório raiz (`/workspace`), a execução deve ser distribuída em **3 terminais distintos**:

**Terminal 1 — Consumidores e Promoções**  
Inicializa os consumidores C1 e C2 juntamente com o publicador periódico de ofertas:

python run_consumidores.py

**Terminal 2 — Micro Serviços de Entrega, Estoque e Pagamento**  
Inicializa os micros serviços exceto principal e promoções que ja foi inicializado aanteriormente :

python run_servicos.py


**Terminal 3 — Micro Serviço Principal**  
Inicializa os consumidores C1 e C2 juntamente com o publicador periódico de ofertas:

python -m ms_principal.main