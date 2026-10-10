# Procedencia de las muestras del Fixture 2030

- `neo4j/*.csv`: repositorio del equipo
  https://github.com/Agusmel03/Grupo-9-Ing-de-datos-2,
  commit `46fd701bac38747804871df0a0974a217f8582ee`. Los equipos conservan
  los ObjectId y codigos de MongoDB del Hito 4. El laboratorio carga los
  campos necesarios para los casos de lectura, no todos los modulos originales.
- `cassandra/esquema.cql`: Hito 6 local del equipo. Particion compuesta por
  partido_id, bucket_10m y shard; clustering por fecha descendente e ID.
  La semilla genera 30 comentarios sinteticos deterministas con el mismo UUID
  en las dos tablas (evita generar UUID distintos por copia desnormalizada).
- Redis: modelo de hashes `fixture2030:session:*` del Hito 7 local;
  la semilla genera una sesion sintetica activa con TTL de 1800 segundos.
- `influx/`: generador y downsampling del repositorio
  https://github.com/Agusmel03/Grupo_9_Hito_8_InfluxDB_Series_Temporales,
  commit `491ece2effd94729404231438701fc7bcdbee806`.
  La muestra tiene 8640 puntos (4 partidos, 2 equipos, 1080 instantes).
- `iris/*.cls`: repositorio
  https://github.com/FacuIria/Hito_9_Grupo_9_IRIS,
  commit `6c82364c542506a111c52153110959e452ddda72`. Se conservan clases,
  herencia, eventos hijos y el metodo de carga de P001.

Los datos son de laboratorio. P001 tiene fechas diferentes entre hitos;
no se corrigen silenciosamente ni se afirma consistencia temporal global.
