import base64
import inspect
import json
import os
from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA
from Crypto.Signature import pkcs1_15


def _resolver_caminho(key_path):
  """Se o caminho não for absoluto, resolve em relação à pasta do script chamador."""
  if os.path.isabs(key_path):
    return key_path

  # Obtém o diretório do script que chamou assinar_payload ou validar_envelope
  frame_chamador = inspect.stack()[2]
  pasta_chamador = os.path.dirname(os.path.abspath(frame_chamador.filename))
  return os.path.join(pasta_chamador, key_path)


def assinar_payload(payload_dict, key_path="private_key.pem"):
  caminho_final = _resolver_caminho(key_path)

  if not os.path.exists(caminho_final):
    raise FileNotFoundError(f"Chave privada não encontrada em: {caminho_final}")

  payload_str = json.dumps(payload_dict, sort_keys=True)
  mensagem_bytes = payload_str.encode("utf-8")

  with open(caminho_final, "rb") as f:
    private_key = RSA.import_key(f.read())

  h = SHA256.new(mensagem_bytes)
  signature_bytes = pkcs1_15.new(private_key).sign(h)
  signature_b64 = base64.b64encode(signature_bytes).decode("utf-8")

  return {"data": payload_dict, "Signature": signature_b64}


def validar_envelope(envelope_str, key_path="public_keys/principal.pem"):
  caminho_final = _resolver_caminho(key_path)

  try:
    envelope = json.loads(envelope_str)
    payload_dict = envelope.get("data")
    signature_b64 = envelope.get("Signature")

    if not payload_dict or not signature_b64:
      return None

    if not os.path.exists(caminho_final):
      print(f" [❌] ERRO: Chave pública não encontrada em: {caminho_final}")
      return None

    with open(caminho_final, "rb") as f:
      public_key = RSA.import_key(f.read())

    payload_str = json.dumps(payload_dict, sort_keys=True)
    mensagem_bytes = payload_str.encode("utf-8")

    h = SHA256.new(mensagem_bytes)
    signature_bytes = base64.b64decode(signature_b64.encode("utf-8"))

    pkcs1_15.new(public_key).verify(h, signature_bytes)
    return payload_dict

  except (ValueError, TypeError) as e:
    print(f" [❌] ERRO na validação: {e}")
    return None