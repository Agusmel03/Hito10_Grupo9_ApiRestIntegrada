import json
from pathlib import Path
from urllib.parse import urlencode

import yaml

from app.main import app

EXAMPLES = [
    ("Grafo completo del Fixture", "/api/v1/grafo", {}, 200),
    ("Equipos", "/api/v1/equipos", {"limite": 10}, 200),
    ("Equipo AAA", "/api/v1/equipos/AAA", {}, 200),
    ("Eventos P001", "/api/v1/partidos/P001/eventos", {}, 200),
    ("Comentarios P001", "/api/v1/partidos/P001/comentarios", {"bucket_10m": "2030-06-10T18:00:00Z", "shard": 0, "limite": 7}, 200),
    ("Sesion vigente", "/api/v1/sesiones/sess-demo-001", {}, 200),
    ("Estadisticas P001", "/api/v1/partidos/P001/estadisticas", {"desde": "2030-06-08T19:00:00Z", "hasta": "2030-06-08T20:30:00Z", "resolucion": "5m"}, 200),
    ("Objeto IRIS", "/api/v1/objetos/partidos/P001", {}, 200),
    ("Entrada invalida", "/api/v1/equipos/aa", {}, 422),
    ("Equipo ausente", "/api/v1/equipos/ZZZ", {}, 404),
    ("Sesion ausente", "/api/v1/sesiones/no-existe", {}, 404),
    ("Particion vacia", "/api/v1/partidos/P999999999/comentarios", {"bucket_10m": "2030-06-10T18:00:00Z", "shard": 0}, 200),
]


def main():
    Path("openapi").mkdir(exist_ok=True)
    Path("openapi/openapi.yaml").write_text(yaml.safe_dump(app.openapi(), sort_keys=False, allow_unicode=True))
    items = []
    for name, path, query, status in EXAMPLES:
        url = "{{base_url}}"+path+("?"+urlencode(query) if query else "")
        items.append({"name": name, "request": {"method": "GET", "header": [], "url": url},
            "event": [{"listen": "test", "script": {"type": "text/javascript", "exec": [
                f'pm.test("HTTP {status}", () => pm.response.to.have.status({status}));',
                'pm.test("Request ID", () => pm.expect(pm.response.headers.get("X-Request-ID")).to.be.a("string"));']}}]})
    collection = {"info": {"name": "Fixture 2030 - Hito 10", "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"},
                  "variable": [{"key": "base_url", "value": "http://localhost:8000"}], "item": items}
    Path("postman/fixture2030_collection.json").write_text(json.dumps(collection, indent=2)+"\n")
    print("OpenAPI y Postman exportados desde la implementacion.")


if __name__ == "__main__":
    main()
