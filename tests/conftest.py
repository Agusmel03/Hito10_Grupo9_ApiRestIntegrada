from datetime import datetime, timezone
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient

from app.config.settings import Settings
from app.main import create_app


@pytest.fixture
def adapters():
    result = {name: Mock() for name in ["mongodb", "neo4j", "cassandra", "redis", "influxdb", "iris"]}
    team = {"id": "000000000000000000000001", "codigo_fifa": "AAA", "nombre": "Seleccion 01", "confederacion": "AFC"}
    result["mongodb"].get_team.return_value = team
    result["mongodb"].list_teams.return_value = [team]
    result["neo4j"].events.return_value = []
    result["cassandra"].comments.return_value = ([], None)
    result["redis"].session.return_value = {"session_id": "sess-demo-001", "estado": "activa", "ttl_segundos": 20}
    result["influxdb"].statistics.return_value = []
    result["iris"].match.return_value = {
        "id": "1", "partido_id": "P001", "equipo_local": "AAA", "equipo_visitante": "AAB",
        "fecha": datetime(2030, 6, 10, 18), "sede": "Estadio Buenos Aires", "estado": "EnCurso",
        "eventos": [], "eventos_truncados": False}
    return result


@pytest.fixture
def client(adapters):
    app = create_app(Settings(_env_file=None, cursor_secret="unit-test-secret-at-least-32-characters"), adapters)
    with TestClient(app, raise_server_exceptions=False) as client:
        yield client
