"""Host entrypoint: build, initialize isolated fixtures and start the local API."""
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent.parent
os.chdir(ROOT)


def run(*args):
    subprocess.run(list(args), check=True)


def main():
    run("docker", "build", "-t", "fixture2030-api:hito10", ".")
    for module in ["scripts.configurar", "scripts.configurar_influx"]:
        run("docker", "run", "--rm", "-v", f"{ROOT}:/app", "fixture2030-api:hito10", "python", "-m", module)
    run("docker", "compose", "-f", "compose.influx.yml", "up", "-d", "--wait", "--wait-timeout", "180")
    run("docker", "compose", "--profile", "lab", "up", "-d", "--wait", "--wait-timeout", "300",
        "mongo", "neo4j", "cassandra", "redis", "iris")
    run(sys.executable, "scripts/inicializar_iris.py")
    for module in ["scripts.sembrar_lab", "scripts.sembrar_influx", "scripts.exportar_contratos"]:
        run("docker", "compose", "run", "--rm", "--no-deps", "api", "python", "-m", module)
    run("docker", "compose", "up", "-d", "--wait", "api")
    print("API iniciada. Swagger: http://localhost:8000/docs (o API_PORT configurado).")


if __name__ == "__main__":
    main()
