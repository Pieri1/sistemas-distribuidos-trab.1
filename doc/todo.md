Infraestrutura e Broker (RabbitMQ)
[X] Criar Exchange eCommerce (tipo Direct).  
[X] Criar Exchange Promoções (tipo Topic).  
[X] Garantir comunicação exclusivamente via eventos (sem chamadas HTTP/RPC diretas).  
[X] Configurar uma fila própria para cada consumidor/microsserviço.  

Segurança e Criptografia (Chave Assimétrica)  
[ ] Gerar pares de chaves pública e privada para cada microsserviço.  
[ ] Criar pastas para cada microsserviço contendo as chaves públicas dos demais.  
[ ] Implementar geração de hash + assinatura digital no envelope (Signature) via chave privada ao publicar eventos.  
[ ] Implementar verificação de integridade/autenticidade via chave pública ao consumir eventos, descartando os inválidos. 

Microsserviço Principal  
[X] Criar interface CLI/Terminal para interação (listar produtos, criar/excluir pedidos, consultar status).  
[X] Publicar evento pedido.criado (Exchange eCommerce).  
(Excluir de fato o status do pedido)
[X] Publicar evento pedido.excluido (quando o estoque for indisponível ou o pagamento for recusado).
[x] Consumir evento pedido.estoque_ok e atualizar status.  
[x] Consumir evento estoque.indisponivel e atualizar status.  
[x] Consumir evento pagamento.aprovado e atualizar status.  
[x] Consumir evento pagamento.recusado e atualizar status.  
[x] Consumir evento pedido.enviado e atualizar status.  

Microsserviço Estoque  
[x] Consumir evento pedido.criado e verificar disponibilidade.  
[x] Publicar evento pedido.estoque_ok se houver estoque suficiente (reservando/baixando itens).  
[x] Publicar evento estoque.indisponivel se faltar item.  
[x] Consumir evento pedido.excluido e devolver os itens reservados ao estoque.  

Microsserviço Pagamento  
[x] Consumir evento pedido.estoque_ok.  
[x] Simular processamento financeiro com aprovação/recusa aleatória.  
[x] Publicar evento pagamento.aprovado.  
[x] Publicar evento pagamento.recusado.  

Microsserviço Entrega  
[x] Consumir evento pagamento.aprovado.  
[x] Simular emissão de nota fiscal e despacho de entrega.  
[x] Publicar evento pedido.enviado.  

Microsserviço Promoções  
[X] Gerar promoções aleatórias contendo categorias de produtos.  
[X] Publicar eventos na Exchange Promoções com routing keys hierárquicas (ex: promocao.categoria.A, promocao.categoria.B, promocao.categoria.C).  

Consumidores de Promoções (Processos Independentes)  
[X] Criar processo Consumidor C1 com fila associada às routing keys das categorias A e B.  
[X] Criar processo Consumidor C2 com fila associada a todas as categorias (promocao.categoria.*).  
[X] Garantir que os consumidores C1 e C2 comuniquem-se apenas com o RabbitMQ (sem chamadas aos microsserviços).  