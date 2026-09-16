import subprocess
import sys
import os
import threading
from pathlib import Path


ROOT = Path(__file__).parent

SCRIPTS = (
    (ROOT / "consumidores" / "c1.py", "\033[36m"),
    (ROOT / "consumidores" / "c2.py", "\033[33m"),
    (ROOT / "ms_promocoes" / "promo.py", "\033[35m"),
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
    print(f"{len(processos)} processos iniciados: c1, c2 e promocoes.")

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