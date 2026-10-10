from neo4j import GraphDatabase, Query
from neo4j.exceptions import DriverError, Neo4jError

from app.observability import guarded


class Neo4jAdapter:
    def __init__(self, settings):
        self.settings = settings
        self.driver = GraphDatabase.driver(settings.neo4j_uri,
            auth=(settings.neo4j_user, settings.neo4j_password.get_secret_value()),
            connection_timeout=settings.timeout_seconds,
            connection_acquisition_timeout=settings.timeout_seconds,
            max_transaction_retry_time=0)

    @guarded("neo4j", (DriverError, Neo4jError))
    def events(self, match_id, offset, limit):
        with self.driver.session(database=self.settings.neo4j_database) as session:
            exists = session.run(Query("MATCH (p:Partido {id_partido:$id}) RETURN p.id_partido AS id",
                                       timeout=self.settings.timeout_seconds), id=match_id).single()
            if not exists:
                return None
            query = Query("""
                MATCH (p:Partido {id_partido:$id})<-[:OCURRE_EN]-(e:Evento)
                OPTIONAL MATCH (e)-[:PROTAGONIZADO_POR]->(j:Jugador)
                RETURN e.id_evento AS id_evento, e.tipo AS tipo, e.minuto AS minuto,
                       e.descripcion AS descripcion, j.mongo_id AS jugador_id
                ORDER BY e.minuto, e.id_evento, j.mongo_id SKIP $offset LIMIT $limit
            """, timeout=self.settings.timeout_seconds)
            return [record.data() for record in session.run(query, id=match_id, offset=offset, limit=limit+1)]

    @guarded("neo4j", (DriverError, Neo4jError))
    def ping(self):
        with self.driver.session(database=self.settings.neo4j_database) as session:
            session.run(Query("RETURN 1", timeout=self.settings.timeout_seconds)).consume()

    def close(self):
        self.driver.close()
