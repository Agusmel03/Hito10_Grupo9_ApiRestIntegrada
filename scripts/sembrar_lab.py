"""Load bounded laboratory samples into the explicitly configured lab containers."""
import csv
from datetime import datetime, timezone, timedelta
from pathlib import Path
from uuid import UUID

from bson import ObjectId
from cassandra.cluster import Cluster
from neo4j import GraphDatabase
from pymongo import MongoClient, UpdateOne
from redis import Redis

from app.config.settings import Settings


def rows(name):
    with Path(f"data/neo4j/{name}.csv").open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def mongo(settings):
    with MongoClient(settings.mongo_uri.get_secret_value(), serverSelectionTimeoutMS=5000) as client:
        db = client[settings.mongo_database]
        db.equipos.create_index("codigo_fifa", unique=True)
        db.equipos.create_index([("confederacion", 1), ("codigo_fifa", 1)])
        operations = []
        for row in rows("equipos"):
            doc = {key: row[key] for key in ["codigo_fifa", "nombre", "confederacion", "entrenador"]}
            doc["ranking_fifa"] = int(row["ranking_fifa"])
            operations.append(UpdateOne({"_id": ObjectId(row["mongo_id"])}, {"$set": doc}, upsert=True))
        db.equipos.bulk_write(operations)
        print(f"MongoDB: {db.equipos.count_documents({})} equipos.")


def neo4j(settings):
    with GraphDatabase.driver(settings.neo4j_uri, auth=(settings.neo4j_user, settings.neo4j_password.get_secret_value())) as driver:
        with driver.session(database=settings.neo4j_database) as session:
            for label, field in [("Partido", "id_partido"), ("Evento", "id_evento"), ("Jugador", "mongo_id"), ("Equipo", "mongo_id"), ("Sede", "id_sede")]:
                session.run(f"CREATE CONSTRAINT IF NOT EXISTS FOR (n:{label}) REQUIRE n.{field} IS UNIQUE").consume()
            session.run("""UNWIND $rows AS row MERGE (p:Partido {id_partido:row.id_partido})
                SET p.fecha=localdatetime(row.fecha), p.fase=row.fase, p.grupo=row.grupo""", rows=rows("partidos")).consume()
            session.run("""UNWIND $rows AS row MERGE (j:Jugador {mongo_id:row.mongo_id})
                SET j += row""", rows=rows("jugadores")).consume()
            session.run("""UNWIND $rows AS row MERGE (e:Equipo {mongo_id:row.mongo_id})
                SET e += row, e.ranking_fifa=toInteger(row.ranking_fifa)""", rows=rows("equipos")).consume()
            session.run("""UNWIND $rows AS row MERGE (s:Sede {id_sede:row.id_sede})
                SET s += row, s.capacidad=toInteger(row.capacidad)""", rows=rows("sedes")).consume()
            session.run("""UNWIND $rows AS row MATCH (p:Partido {id_partido:row.id_partido})
                MATCH (a:Equipo {mongo_id:row.equipo_local_id}), (b:Equipo {mongo_id:row.equipo_visitante_id}), (s:Sede {id_sede:row.sede_id})
                MERGE (a)-[:PARTICIPA_EN {rol:'LOCAL'}]->(p)
                MERGE (b)-[:PARTICIPA_EN {rol:'VISITANTE'}]->(p)
                MERGE (p)-[:SE_JUEGA_EN]->(s)""", rows=rows("partidos")).consume()
            session.run("""MATCH (j:Jugador), (e:Equipo) WHERE j.equipo_id=e.mongo_id
                MERGE (j)-[:PERTENECE_A]->(e)""").consume()
            session.run("""UNWIND $rows AS row
                MATCH (p:Partido {id_partido:row.partido_id})
                MATCH (j:Jugador {mongo_id:row.jugador_id})
                MERGE (e:Evento {id_evento:row.id_evento})
                SET e.tipo=row.tipo, e.minuto=toInteger(row.minuto), e.descripcion=row.descripcion
                MERGE (e)-[:OCURRE_EN]->(p) MERGE (e)-[:PROTAGONIZADO_POR]->(j)""", rows=rows("eventos")).consume()
            print("Neo4j: partidos, jugadores y eventos originales cargados.")


def cassandra(settings):
    cluster = Cluster([settings.cassandra_host], port=settings.cassandra_port, connect_timeout=5)
    try:
        session = cluster.connect()
        session.execute("""CREATE KEYSPACE IF NOT EXISTS fixture2030_comentarios
            WITH replication = {'class':'NetworkTopologyStrategy','datacenter1':1}""")
        session.set_keyspace(settings.cassandra_keyspace)
        session.execute("""CREATE TABLE IF NOT EXISTS comentarios_por_partido (
            partido_id text, bucket_10m timestamp, shard int, creado_en timestamp,
            comentario_id uuid, usuario_id text, contenido text,
            PRIMARY KEY ((partido_id,bucket_10m,shard),creado_en,comentario_id))
            WITH CLUSTERING ORDER BY (creado_en DESC, comentario_id ASC)""")
        session.execute("""CREATE TABLE IF NOT EXISTS comentarios_por_usuario (
            usuario_id text, mes_bucket text, creado_en timestamp, comentario_id uuid,
            partido_id text, contenido text, PRIMARY KEY ((usuario_id,mes_bucket),creado_en,comentario_id))
            WITH CLUSTERING ORDER BY (creado_en DESC, comentario_id ASC)""")
        by_match = session.prepare("INSERT INTO comentarios_por_partido (partido_id,bucket_10m,shard,creado_en,comentario_id,usuario_id,contenido) VALUES (?,?,?,?,?,?,?)")
        by_user = session.prepare("INSERT INTO comentarios_por_usuario (usuario_id,mes_bucket,creado_en,comentario_id,partido_id,contenido) VALUES (?,?,?,?,?,?)")
        bucket = datetime(2030, 6, 10, 18, tzinfo=timezone.utc)
        for i in range(30):
            when = bucket+timedelta(seconds=i*5)
            cid = UUID(int=i+1)
            content = f"Comentario de laboratorio {i+1} del Fixture 2030"
            session.execute(by_match, ("P001", bucket, 0, when, cid, "USR001", content))
            session.execute(by_user, ("USR001", "2030-06", when, cid, "P001", content))
        print("Cassandra: 30 comentarios, misma identidad en ambas tablas.")
    finally:
        cluster.shutdown()


def redis(settings):
    client = Redis.from_url(settings.redis_url.get_secret_value())
    try:
        with client.pipeline(transaction=True) as pipe:
            pipe.hset("fixture2030:session:sess-demo-001", mapping={
                "session_id": "sess-demo-001", "usuario_id": "USR000001", "estado": "activa",
                "ultima_actividad": "2030-06-10T18:00:00Z", "origen": "web"})
            pipe.expire("fixture2030:session:sess-demo-001", 1800).execute()
        print("Redis: sesion de muestra con TTL 1800 segundos.")
    finally:
        client.close()


if __name__ == "__main__":
    s = Settings()
    # Refuse accidental loading into a personal or production environment.
    if not (s.mongo_uri.get_secret_value() == "mongodb://mongo:27017"
            and s.neo4j_uri == "bolt://neo4j:7687" and s.cassandra_host == "cassandra"
            and s.redis_url.get_secret_value() == "redis://redis:6379/0"):
        raise SystemExit("Este script solo carga los contenedores del laboratorio Compose.")
    mongo(s)
    neo4j(s)
    cassandra(s)
    redis(s)
