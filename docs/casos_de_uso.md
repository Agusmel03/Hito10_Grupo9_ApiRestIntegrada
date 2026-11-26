# Casos de uso - decisiones previas a las rutas

Consumidor: una aplicacion del Fixture Mundial 2030 o un integrante del equipo
que consulta Swagger. API local de laboratorio, sin datos personales reales.

| Caso | Entrada | Fuente y patron | Exito | Ausencia | Falla |
|---|---|---|---|---|---|
| Listar equipos | codigo posterior, limite, confederacion | MongoDB; indice de codigo FIFA | pagina ordenada, 200 | lista vacia, 200 | 503 |
| Detalle de equipo | codigo FIFA | MongoDB; igualdad unica | campos publicos, 200 | 404 | 503 |
| Eventos de partido | ID, limite, offset acotado | Neo4j; Partido <- OCURRE_EN - Evento | eventos y protagonistas, 200 | partido 404; sin eventos 200 | 503 |
| Comentarios por particion | partido, bucket de 10 minutos, shard, cursor | Cassandra; clave de particion completa | pagina y cursor, 200 | particion vacia, 200 | 503 |
| Consultar sesion | identificador | Redis; hash fixture2030:session:* | estado y TTL vigente, 200 | ausente/expirada, 404 | 503 |
| Estadisticas por ventana | partido, equipo opcional, desde, hasta, resolucion | InfluxDB; Flux acotado por tags y tiempo | agregaciones por field, 200 | sin puntos, 200 | 503 |
| Publicar comentario | partido; usuario y contenido en el cuerpo | Cassandra; LOGGED BATCH en comentarios_por_partido y comentarios_por_usuario | comentario con bloque y shard, 201 | no aplica | 503 |
| Detalle de objeto partido | PartidoID, limite de eventos | IRIS; indice unico y relacion padre-hijo | objeto publico con eventos, 200 | 404 | 503 |

La API implementa lectura en las seis fuentes y una escritura en Cassandra.
El POST de comentarios escribe las dos tablas desnormalizadas en un LOGGED BATCH:
Cassandra garantiza que ambas inserciones se aplican o ninguna, aunque no de forma
aislada (un lector puede ver una tabla actualizada un instante antes que la otra).
La particion es (partido_id, bucket_10m, shard): bucket_10m es el bloque de 10
minutos UTC del instante de creacion y shard el resto de dividir comentario_id
(un UUID, numero de 128 bits) por 8. No se valida la existencia del partido en
otros motores.
La consigna permite lecturas y escrituras cuando correspondan al caso de uso.
Todos los GET son idempotentes y no renuevan TTL ni modifican datos. El POST no es idempotente: cada llamada crea un comentario nuevo.
No hay transiciones IRIS ni conflicto de escritura 409 en este contrato.

No se exige consistencia global entre motores: P001 tiene fechas diferentes
en las muestras de Neo4j/InfluxDB y Cassandra/IRIS. Se preservan las fechas
de cada hito y se documenta esa diferencia; no se presenta una vista unificada
que afirme que las muestras son un unico partido sincronizado.
