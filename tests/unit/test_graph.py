from app.errors import unavailable


def test_graph_contract(client, adapters):
    graph = {"nodos": [{"id": "n1", "tipo": "Equipo", "propiedades": {"codigo_fifa": "AAA"}}],
             "relaciones": [], "total_nodos": 1, "truncado": False}
    adapters["neo4j"].graph.return_value = graph
    response = client.get("/api/v1/grafo")
    assert response.status_code == 200
    assert response.json()["data"] == graph
    assert response.headers["X-Request-ID"]


def test_graph_failure_is_safe(client, adapters):
    adapters["neo4j"].graph.side_effect = unavailable("neo4j")
    response = client.get("/api/v1/grafo")
    assert response.status_code == 503
    assert response.json()["error"]["dependency"] == "neo4j"


def test_empty_graph(client, adapters):
    adapters["neo4j"].graph.return_value = {"nodos": [], "relaciones": [], "total_nodos": 0, "truncado": False}
    assert client.get("/api/v1/grafo").json()["data"]["nodos"] == []
