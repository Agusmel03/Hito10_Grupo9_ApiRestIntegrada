"""Keep only structured application logs correlated with the HTTP report."""
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parent.parent
report = json.loads((ROOT / "docs/evidencia/http_verificacion.json").read_text())
ids = {result["request_id"] for result in report["results"]}
result = subprocess.run(["docker", "compose", "logs", "--no-color", "--no-log-prefix", "api"],
                        cwd=ROOT, text=True, capture_output=True, check=True)
records = []
allowed = {"request_id", "dependency", "operation", "result", "error_type", "duration_ms", "method", "route", "status"}
for line in result.stdout.splitlines():
    try:
        record = json.loads(line)
    except ValueError:
        continue
    if isinstance(record, dict) and record.get("request_id") in ids:
        records.append({key: value for key, value in record.items() if key in allowed})
sources = {record.get("dependency") for record in records}
required = {"mongodb", "neo4j", "cassandra", "redis", "influxdb", "iris"}
if not required.issubset(sources):
    raise SystemExit("Faltan logs correlacionados de alguna fuente; repetir verificacion HTTP.")
(ROOT / "docs/evidencia/correlacion.json").write_text(json.dumps(records, indent=2)+"\n")
print(f"{len(records)} registros correlacionados; seis fuentes verificadas.")
