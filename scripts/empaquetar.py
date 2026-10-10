"""Build a source delivery archive from an explicit allowlist, without secrets."""
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parent.parent
files = ["README.md", "Dockerfile", ".dockerignore", ".gitignore", ".env.example",
         "requirements.txt", "pytest.ini", "compose.yml", "compose.influx.yml"]
directories = ["app", "scripts", "tests", "data", "docs", "openapi", "postman"]
paths = [ROOT / name for name in files]
for name in directories:
    paths.extend(p for p in (ROOT/name).rglob("*") if p.is_file()
                 and "__pycache__" not in p.parts and "generated" not in p.parts
                 and p.suffix not in {".pyc", ".log"} and not p.name.startswith(".env"))
output = ROOT / "output" / "Grupo_9_Hito_10_API_REST.zip"
output.parent.mkdir(exist_ok=True)
with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
    for path in sorted(paths):
        archive.write(path, "Grupo_9_Hito_10_API_REST/"+str(path.relative_to(ROOT)))
with zipfile.ZipFile(output) as archive:
    assert archive.testzip() is None
    assert not any(Path(name).name == ".env" or ".git/" in name for name in archive.namelist())
print(f"Entrega creada: {output.name} ({len(paths)} archivos). No incluye .env ni volumenes.")
