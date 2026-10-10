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
| Detalle de objeto partido | PartidoID, limite de eventos | IRIS; indice unico y relacion padre-hijo | objeto publico con eventos, 200 | 404 | 503 |

Esta primera version implementa lectura en las seis fuentes. Cassandra conserva
la particion (partido_id, bucket_10m, shard); no se inventa un POST antes de
definir una garantia consistente entre sus dos tablas desnormalizadas.
La consigna permite lecturas y escrituras cuando correspondan al caso de uso.
Todos los GET son idempotentes y no renuevan TTL ni modifican datos.
No hay transiciones IRIS ni conflicto de escritura 409 en este contrato.

No se exige consistencia global entre motores: P001 tiene fechas diferentes
en las muestras de Neo4j/InfluxDB y Cassandra/IRIS. Se preservan las fechas
de cada hito y se documenta esa diferencia; no se presenta una vista unificada
que afirme que las muestras son un unico partido sincronizado.
