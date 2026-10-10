"""Run from the host; return nonzero if any verification fails."""
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent.parent
for command in [
    ["docker", "compose", "run", "--rm", "--no-deps", "-e", "RUN_INTEGRATION=1", "api", "python", "-m", "pytest", "-q", "--junitxml=docs/evidencia/pytest.xml"],
    ["docker", "compose", "run", "--rm", "--no-deps", "api", "python", "-m", "scripts.verificar_conectividad"],
    [sys.executable, "scripts/capturar_logs.py"],
]:
    subprocess.run(command, cwd=ROOT, check=True)
