import os
from Crypto.PublicKey import RSA

# 1. Descobre o nome da pasta atual (ex: 'ms_estoque', 'ms_pagamento')
current_dir_name = os.path.basename(os.getcwd())

# 2. Remove o prefixo "ms_" se existir, para obter o nome base (ex: 'estoque', 'pagamento')
if current_dir_name.startswith("ms_"):
  service_name = current_dir_name[3:]
else:
  service_name = current_dir_name

# Garante que a pasta public_keys existe
os.makedirs("public_keys", exist_ok=True)

# 3. Gera o par de chaves RSA de 2048 bits
key = RSA.generate(2048)

# 4. Salva a chave privada do próprio microsserviço na raiz da pasta
with open("private_key.pem", "wb") as f:
  f.write(key.export_key())
print(f" [✓] Chave privada gerada: private_key.pem")

# 5. Salva a chave pública própria dentro de public_keys usando o nome dinâmico
public_key_path = os.path.join("public_keys", f"{service_name}.pem")
with open(public_key_path, "wb") as f:
  f.write(key.publickey().export_key())

print(
    f" [✓] Chave pública própria gerada e salva em: {public_key_path} (Pronta"
    " para ser copiada para os outros microsserviços)"
)