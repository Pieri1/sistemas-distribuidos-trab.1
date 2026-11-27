import subprocess
import sys
import os
import threading
from pathlib import Path


ROOT = Path(__file__).parent

SCRIPTS = (
    (ROOT / "ms_estoque" / "estoque.py", "\033[32m"),         # Verde (Porta 8001)
    (ROOT / "ms_pagamento" / "pagamento.py", "\033[31m"),     # Vermelho (Porta 8002)
    (ROOT / "mock_pagamento" / "mock_pagamento.py", "\033[33m"),  # Amarelo (Porta 8003)
    (ROOT / "ms_entrega" / "entrega.py", "\033[34m"),         # Azul
    (ROOT / "ms_promocoes" / "promo.py", "\033[35m"),         # Magenta
    (ROOT / "ms_principal" / "main.py", "\033[36m"),          # Ciano (API Gateway - Porta 8000)
)
RESET = "\033[0m"


def acompanhar_log(processo, script, cor):
    for linha in processo.stdout:
        prefixo = f"[{script.parent.name}/{script.name}]"
        print(f"{cor}{prefixo} {linha}{RESET}", end="", flush=True)


def iniciar(script, cor):
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT)

    processo = subprocess.Popen(
        [sys.executable, "-u", str(script)],
        cwd=ROOT,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    threading.Thread(
        target=acompanhar_log,
        args=(processo, script, cor),
        daemon=True,
    ).start()
    return processo


def main():
    processos = [iniciar(script, cor) for script, cor in SCRIPTS]
    print(
        f"{len(processos)} serviços iniciados: "
        "ms_estoque (8001), ms_pagamento (8002), mock_pagamento (8003), "
        "ms_entrega, ms_promocoes e ms_principal/API Gateway (8000)."
    )

    try:
        for processo in processos:
            processo.wait()
    except KeyboardInterrupt:
        for processo in processos:
            processo.terminate()
        for processo in processos:
            processo.wait()


if __name__ == "__main__":
    main()