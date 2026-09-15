import shutil
import subprocess
import sys
import threading
from pathlib import Path


ROOT = Path(__file__).parent


def encontrar_scripts():
	return sorted(
		list(ROOT.glob("ms_*/*.py"))
		+ list((ROOT / "consumidores").glob("*.py"))
	)


def abrir_terminal(script):
	terminal = shutil.which("x-terminal-emulator") or shutil.which("gnome-terminal")
	comando = f'cd "{script.parent}" && "{sys.executable}" -u "{script.name}"; exec bash'

	if terminal:
		if Path(terminal).name == "gnome-terminal":
			return subprocess.Popen([terminal, "--", "bash", "-lc", comando])
		return subprocess.Popen([terminal, "-e", "bash", "-lc", comando])

	processo = subprocess.Popen(
		[sys.executable, "-u", str(script)],
		cwd=script.parent,
		stdout=subprocess.PIPE,
		stderr=subprocess.STDOUT,
		text=True,
		bufsize=1,
	)

	def mostrar_log():
		for linha in processo.stdout:
			print(f"[{script.parent.name}/{script.name}] {linha}", end="", flush=True)

	threading.Thread(target=mostrar_log, daemon=True).start()
	return processo


def main():
	scripts = encontrar_scripts()
	if not scripts:
		print("Nenhum script foi encontrado.")
		return

	processos = [abrir_terminal(script) for script in scripts]
	print(f"{len(processos)} serviços iniciados.")

	try:
		for processo in processos:
			processo.wait()
	except KeyboardInterrupt:
		for processo in processos:
			processo.terminate()


if __name__ == "__main__":
	main()
