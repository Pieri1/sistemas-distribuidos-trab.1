import subprocess
import sys
import os
import threading
from pathlib import Path


ROOT = Path(__file__).parent

SCRIPTS = (
    (ROOT / "ms_estoque" / "estoque.py", "\033[32m"),
    (ROOT / "ms_entrega" / "entrega.py", "\033[34m"),
    (ROOT / "ms_pagamento" / "pagamento.py", "\033[31m"),
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
    print(f"{len(processos)} processos iniciados: estoque, entrega e pagamento.")

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