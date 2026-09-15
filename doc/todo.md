Infraestrutura e Broker (RabbitMQ)
[ ] Criar Exchange eCommerce (tipo Direct).  
[ ] Criar Exchange Promoções (tipo Topic).  
[ ] Garantir comunicação exclusivamente via eventos (sem chamadas HTTP/RPC diretas).  
[ ] Configurar uma fila própria para cada consumidor/microsserviço.  

Segurança e Criptografia (Chave Assimétrica)  
[ ] Gerar pares de chaves pública e privada para cada microsserviço.  
[ ] Criar pastas para cada microsserviço contendo as chaves públicas dos demais.  
[ ] Implementar geração de hash + assinatura digital no envelope (Signature) via chave privada ao publicar eventos.  
[ ] Implementar verificação de integridade/autenticidade via chave pública ao consumir eventos, descartando os inválidos. 

Microsserviço Principal  
[ ] Criar interface CLI/Terminal para interação (listar produtos, criar/excluir pedidos, consultar status).  
[ ] Publicar evento pedido.criado (Exchange eCommerce).  
[ ] Publicar evento pedido.excluido (quando o estoque for indisponível ou o pagamento for recusado).  
[ ] Consumir evento pedido.estoque_ok e atualizar status.  
[ ] Consumir evento estoque.indisponivel e atualizar status.  
[ ] Consumir evento pagamento.aprovado e atualizar status.  
[ ] Consumir evento pagamento.recusado e atualizar status.  
[ ] Consumir evento pedido.enviado e atualizar status.  

Microsserviço Estoque  
[ ] Consumir evento pedido.criado e verificar disponibilidade.  
[ ] Publicar evento pedido.estoque_ok se houver estoque suficiente (reservando/baixando itens).  
[ ] Publicar evento estoque.indisponivel se faltar item.  
[ ] Consumir evento pedido.excluido e devolver os itens reservados ao estoque.  

Microsserviço Pagamento  
[ ] Consumir evento pedido.estoque_ok.  
[ ] Simular processamento financeiro com aprovação/recusa aleatória.  
[ ] Publicar evento pagamento.aprovado.  
[ ] Publicar evento pagamento.recusado.  

Microsserviço Entrega  
[ ] Consumir evento pagamento.aprovado.  
[ ] Simular emissão de nota fiscal e despacho de entrega.  
[ ] Publicar evento pedido.enviado.  

Microsserviço Promoções  
[ ] Gerar promoções aleatórias contendo categorias de produtos.  
[ ] Publicar eventos na Exchange Promoções com routing keys hierárquicas (ex: promocao.categoria.A, promocao.categoria.B, promocao.categoria.C).  

Consumidores de Promoções (Processos Independentes)  
[ ] Criar processo Consumidor C1 com fila associada às routing keys das categorias A e B.  
[ ] Criar processo Consumidor C2 com fila associada a todas as categorias (promocao.categoria.*).  
[ ] Garantir que os consumidores C1 e C2 comuniquem-se apenas com o RabbitMQ (sem chamadas aos microsserviços).  