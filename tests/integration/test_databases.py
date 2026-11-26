import os
import time
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from jsonschema import Draft202012Validator
from redis import Redis

from app.config.settings import Settings
from app.main import create_app

pytestmark = [pytest.mark.integration, pytest.mark.skipif(os.getenv("RUN_INTEGRATION") != "1", reason="RUN_INTEGRATION=1 requiere bases del laboratorio")]


@pytest.fixture(scope="module")
def live_client():
    with TestClient(create_app(Settings()), raise_server_exceptions=False) as client:
        yield client


@pytest.mark.parametrize("url,key", [
    ("/api/v1/grafo", "nodos"),
    ("/api/v1/equipos/AAA", "codigo_fifa"),
    ("/api/v1/partidos/P001/eventos", "items"),
    ("/api/v1/partidos/P001/comentarios?bucket_10m=2030-06-10T18:00:00Z&shard=0", "items"),
    ("/api/v1/sesiones/sess-demo-001", "ttl_segundos"),
    ("/api/v1/partidos/P001/estadisticas?desde=2030-06-08T19:00:00Z&hasta=2030-06-08T20:30:00Z", "items"),
    ("/api/v1/objetos/partidos/P001", "partido_id"),
])
def test_real_source_and_schema(live_client, url, key):
    if "/objetos/" in url and not Settings().iris_password.get_secret_value():
        pytest.skip("IRIS: falta credencial local; no se afirma integracion verificada")
    response = live_client.get(url)
    assert response.status_code == 200, response.text
    assert response.json()["data"][key]
    route = next(r for r in live_client.app.routes if hasattr(r, "path_regex") and r.path_regex.fullmatch(url.split("?")[0]))
    spec = live_client.app.openapi()
    schema = spec["paths"][route.path]["get"]["responses"]["200"]["content"]["application/json"]["schema"]
    Draft202012Validator({**schema, "components": spec["components"]}).validate(response.json())


def test_real_cassandra_pagination(live_client):
    path = "/api/v1/partidos/P001/comentarios"
    ids = []
    for shard in range(8):
        params = {"bucket_10m": "2030-06-10T18:00:00Z", "shard": shard, "limite": 2}
        shard_ids = []
        for _ in range(10):
            response = live_client.get(path, params=params)
            assert response.status_code == 200, response.text
            data = response.json()["data"]
            assert data["shard"] == shard and len(data["items"]) <= 2
            shard_ids.extend(row["comentario_id"] for row in data["items"])
            if not data["siguiente_cursor"]:
                break
            params["cursor"] = data["siguiente_cursor"]
        # Cada comentario esta en el shard que indica el resto de dividir su numero por 8.
        assert all(UUID(cid).int % 8 == shard for cid in shard_ids)
        ids.extend(shard_ids)
    assert len(ids) == len(set(ids)) == 30


def test_complete_lab_graph(live_client):
    response = live_client.get("/api/v1/grafo")
    assert response.status_code == 200, response.text
    data = response.json()["data"]
    assert data["truncado"] is False
    assert len(data["nodos"]) == data["total_nodos"]
    assert {n["tipo"] for n in data["nodos"]} == {"Partido", "Equipo", "Jugador", "Sede", "Evento"}
    ids = {n["id"] for n in data["nodos"]}
    assert len(ids) == len(data["nodos"])
    assert all(r["origen"] in ids and r["destino"] in ids for r in data["relaciones"])
    assert {r["tipo"] for r in data["relaciones"]} == {"PARTICIPA_EN", "SE_JUEGA_EN", "PERTENECE_A", "OCURRE_EN", "PROTAGONIZADO_POR"}
    player = next(n for n in data["nodos"] if n["tipo"] == "Jugador")
    assert "club" in player["propiedades"]


def test_real_mongo_keyset(live_client):
    first = live_client.get("/api/v1/equipos?limite=1").json()["data"]
    second = live_client.get("/api/v1/equipos", params={"limite": 1, "despues": first["siguiente_codigo"]}).json()["data"]
    assert first["items"][0]["codigo_fifa"] == "AAA"
    assert second["items"][0]["codigo_fifa"] == "AAB"


def test_iris_child_relation_limits_and_absence(live_client):
    response = live_client.get("/api/v1/objetos/partidos/P001?limite_eventos=1")
    assert response.status_code == 200, response.text
    data = response.json()["data"]
    assert len(data["eventos"]) == 1
    assert data["eventos"][0]["tipo"] == "Gol"
    assert data["eventos_truncados"] is True
    assert live_client.get("/api/v1/objetos/partidos/P999999999").status_code == 404


def test_real_absence_and_empty_results(live_client):
    for url in ["/api/v1/equipos/ZZZ", "/api/v1/partidos/P999999999/eventos", "/api/v1/sesiones/no-existe"]:
        assert live_client.get(url).status_code == 404
    response = live_client.get("/api/v1/partidos/P999999999/estadisticas?desde=2030-06-08T19:00:00Z&hasta=2030-06-08T20:30:00Z")
    assert response.status_code == 200
    assert response.json()["data"]["items"] == []


def test_redis_real_expiration(live_client):
    s = Settings()
    if s.redis_url.get_secret_value() != "redis://redis:6379/0":
        pytest.skip("La prueba con escritura solo se permite en Redis del laboratorio")
    redis = Redis.from_url(s.redis_url.get_secret_value())
    key = "fixture2030:session:hito10-expiration-test"
    try:
        with redis.pipeline() as pipe:
            pipe.hset(key, mapping={"estado": "activa"}).expire(key, 1).execute()
        assert live_client.get("/api/v1/sesiones/hito10-expiration-test").status_code == 200
        time.sleep(1.2)
        assert live_client.get("/api/v1/sesiones/hito10-expiration-test").status_code == 404
    finally:
        redis.delete(key)
        redis.close()


@pytest.mark.parametrize("source,overrides,path", [
    ("mongodb", {"mongo_uri": "mongodb://127.0.0.1:1"}, "/api/v1/equipos/AAA"),
    ("neo4j", {"neo4j_uri": "bolt://127.0.0.1:1"}, "/api/v1/partidos/P001/eventos"),
    ("cassandra", {"cassandra_host": "127.0.0.1", "cassandra_port": 1}, "/api/v1/partidos/P001/comentarios?bucket_10m=2030-06-10T18:00:00Z&shard=0"),
    ("redis", {"redis_url": "redis://127.0.0.1:1/0"}, "/api/v1/sesiones/sess-demo-001"),
    ("influxdb", {"influx_url": "http://127.0.0.1:1"}, "/api/v1/partidos/P001/estadisticas?desde=2030-06-08T19:00:00Z&hasta=2030-06-08T20:30:00Z"),
    ("iris", {"iris_host": "127.0.0.1", "iris_port": 1}, "/api/v1/objetos/partidos/P001"),
])
def test_real_unreachable_dependency_is_bounded(source, overrides, path):
    settings = Settings(timeout_seconds=1, **overrides)
    with TestClient(create_app(settings), raise_server_exceptions=False) as client:
        start = time.perf_counter()
        response = client.get(path)
        elapsed = time.perf_counter()-start
    assert response.status_code == 503, response.text
    assert response.json()["error"]["dependency"] == source
    assert elapsed < 5


def test_influx_semantics(live_client):
    response = live_client.get("/api/v1/partidos/P001/estadisticas?desde=2030-06-08T19:00:00Z&hasta=2030-06-08T20:30:00Z&resolucion=5m&equipo=AAA")
    assert response.status_code == 200, response.text
    rows = response.json()["data"]["items"]
    assert len(rows) == 18
    assert all(0 <= row["posesion_pct"] <= 100 for row in rows)
    passes = [row["pases_completados_total"] for row in rows]
    assert passes == sorted(passes)
    assert all(row["tiros_intervalo"] >= 0 for row in rows)
