# Tutorial 5: Integração com API Externa de E-mail (Resend via REST)

## Onde você vai usar isso no Trabalho 2?
No **MS Promoções** (vale **0,4 ponto**):
- No Trabalho 1, os consumidores `c1.py` e `c2.py` ficavam ouvindo o RabbitMQ no terminal.
- Agora no Trabalho 2, o usuário cadastra seu **e-mail** e as **categorias de interesse** (`A`, `B`, `C`) no Frontend -> o API Gateway publica o evento `interesse.promocao` no RabbitMQ -> o **MS Promoções** consome esse evento, guarda os e-mails interessados em cada categoria e, quando sorteia uma promoção, **dispara um e-mail real** usando uma API Externa de E-mail (como o **Resend**)!

---

## Como funciona a API do Resend?
O **Resend** (`https://resend.com`) é um serviço gratuito (permite até 100 e-mails/dia no plano grátis) que expõe um endpoint REST super simples:
- **Método e URL**: `POST https://api.resend.com/emails`
- **Header de Autenticação**: `Authorization: Bearer re_SUA_CHAVE_AQUI`
- **Remetente padrão de testes**: `onboarding@resend.dev` (você não precisa ter domínio próprio! No modo gratuito de teste, ele envia para o mesmo endereço de e-mail que você usou para criar sua conta no Resend).

---

## Como Testar este Tutorial

1. Execute o script diretamente para ver como o payload HTTP é montado (modo simulação sem chave, ou modo real se você definir a variável `RESEND_API_KEY`):
```bash
python enviar_email_resend.py
```

2. Quando quiser testar enviando para o seu e-mail real:
   - Crie uma conta gratuita em `https://resend.com` e gere uma **API Key**.
   - Exporte a chave no terminal e rode:
```bash
export RESEND_API_KEY="re_sua_chave_aqui"
export EMAIL_DESTINO="seu_email_cadastrado_no_resend@gmail.com"
python enviar_email_resend.py
```

