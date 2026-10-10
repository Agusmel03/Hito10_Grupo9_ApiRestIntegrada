-- =====================================================
-- HITO 6 - CASSANDRA
-- Grupo 9 - Fixture 2030
-- Esquema para comentarios masivos
-- =====================================================


-- =====================================================
-- 1. KEYSPACE
-- =====================================================

CREATE KEYSPACE IF NOT EXISTS fixture2030_comentarios
WITH replication = {
    'class': 'NetworkTopologyStrategy',
    'datacenter1': 1
}
AND durable_writes = true;


USE fixture2030_comentarios;


-- =====================================================
-- 2. TABLA PRINCIPAL
-- Comentarios de un partido ordenados por fecha
--
-- Partition Key:
-- partido_id + bucket_10m + shard
--
-- El bucket temporal y el shard evitan que un partido
-- muy popular genere una unica particion ilimitada.
-- =====================================================

CREATE TABLE IF NOT EXISTS comentarios_por_partido (

    partido_id text,

    bucket_10m timestamp,

    shard int,

    creado_en timestamp,

    comentario_id uuid,

    usuario_id text,

    contenido text,

    PRIMARY KEY (
        (partido_id, bucket_10m, shard),
        creado_en,
        comentario_id
    )
)
WITH CLUSTERING ORDER BY (
    creado_en DESC,
    comentario_id ASC
);


-- =====================================================
-- 3. TABLA SECUNDARIA ORIENTADA A CONSULTA
-- Comentarios realizados por un usuario.
--
-- En Cassandra se duplica informacion cuando responde
-- a un patron de acceso diferente.
-- =====================================================

CREATE TABLE IF NOT EXISTS comentarios_por_usuario (

    usuario_id text,

    mes_bucket text,

    creado_en timestamp,

    comentario_id uuid,

    partido_id text,

    contenido text,

    PRIMARY KEY (
        (usuario_id, mes_bucket),
        creado_en,
        comentario_id
    )
)
WITH CLUSTERING ORDER BY (
    creado_en DESC,
    comentario_id ASC
);


-- =====================================================
-- 4. VERIFICACION
-- =====================================================

DESCRIBE KEYSPACE fixture2030_comentarios;

DESCRIBE TABLE fixture2030_comentarios.comentarios_por_partido;

DESCRIBE TABLE fixture2030_comentarios.comentarios_por_usuario;
