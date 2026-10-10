"""Collect reproducible HTTP evidence without tokens or private configuration."""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
from time import perf_counter

import httpx

from scripts.exportar_contratos import EXAMPLES


def main():
    base = os.getenv("API_BASE_URL", "http://api:8000")
    results = []
    with httpx.Client(base_url=base, timeout=40) as client:
        for name, path, params, expected in EXAMPLES:
            start = perf_counter()
            response = client.get(path, params=params)
            data = response.json()
            results.append({"case": name, "path": path, "query": params, "expected": expected,
                "actual": response.status_code, "passed": response.status_code == expected,
                "duration_ms": round((perf_counter()-start)*1000, 2),
                "request_id": response.headers.get("X-Request-ID"), "response": data})
        health = client.get("/api/v1/salud")
    report = {"timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "method": "HTTP GET secuencial; una request por caso, sin calentamiento ni concurrencia",
        "environment": "Docker Desktop ARM64; cliente y API en contenedores; laboratorio local",
        "limitations": "Muestra pequena; no es un benchmark de capacidad. Latencia incluye HTTP y consulta.",
        "results": results, "health_status": health.status_code, "health": health.json()}
    destination = Path("docs/evidencia/http_verificacion.json")
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(report, indent=2)+"\n")
    for result in results:
        print(f'{result["case"]}: HTTP {result["actual"]}; esperado {result["expected"]}')
    print(f"Salud: HTTP {health.status_code}; evidencia en {destination}")
    return 0 if all(r["passed"] for r in results) and health.status_code == 200 else 1


if __name__ == "__main__":
    raise SystemExit(main())
