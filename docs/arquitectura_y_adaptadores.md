# Arquitectura y adaptadores

Flujo: cliente HTTP -> `app/routes/api.py` -> `app/services/fixture.py` ->
adaptador en `app/adapters/` -> driver -> motor. Pydantic define y valida los
contratos en `app/schemas/models.py`; `app/config/settings.py` lee el entorno.
La aplicacion crea clientes en su ciclo de vida y los cierra al terminar.
Las rutas sincronicas se ejecutan en el pool de threads de FastAPI; el endpoint
de salud consulta fuentes en paralelo sin bloquear el event loop.

| Adaptador | Contexto y acceso | Transformacion |
|---|---|---|
| MongoDB / PyMongo | `fixture2030.equipos`; codigo FIFA unico, proyeccion y paginacion por clave | ObjectId a texto; solo campos publicos |
| Neo4j / driver oficial | database configurada; Cypher parametrizado, relacion OCURRE_EN y PROTAGONIZADO_POR | nodos y relaciones a eventos con ID de protagonista |
| Cassandra / cassandra-driver | keyspace del Hito 6, prepared statement y particion completa | current_rows; paging_state firmado y acotado |
| Redis / redis-py | hash fixture2030:session:ID; HGETALL y TTL en transaccion | excluye usuario, origen y otros datos internos |
| InfluxDB / influxdb-client | bucket estadisticas_live; tags, intervalo y agregaciones Flux | pivot de fields en puntos publicos |
| IRIS / intersystems-irispython | namespace USER; vista SQL de clases persistentes y relacion padre-hijo | preserva ID interno, PartidoID, fecha y eventos |

IRIS usa SQL parametrizado sobre las clases originales. No modifica el modelo
de objetos ni saltea sus reglas de escritura: esta API solo lee. Cada consulta
abre una conexion y la cierra, sin compartir cursores entre threads.

Cassandra conecta de forma diferida y protege la primera conexion con un lock.
El cursor incluye particion, tamanio de pagina y vencimiento; una firma HMAC evita
usar un paging_state arbitrario. No se itera el ResultSet completo, porque eso
activaria la descarga automatica de todas las paginas.

El servicio distingue un recurso ausente de un conjunto vacio. Una falla del
driver se traduce en 503; un error de programacion conserva 500. Ninguna ruta
acepta nombres libres de tablas, comandos, Cypher, Flux o consultas SQL.

Observabilidad: cada request lleva X-Request-ID (UUID). Los logs JSON registran
la plantilla de ruta, metodo, estado HTTP y duracion. Los adaptadores agregan
fuente, operacion, resultado y clase de error. No se registran URI, contrasenas,
tokens, query strings, contenido de sesiones ni mensajes completos del driver.

Se conserva la separacion entre modelos: no existe una transaccion global ni
un endpoint que mezcle seis fuentes sin un caso de uso. Los datos de los hitos
no estan sincronizados temporalmente y no se afirma que lo esten.
