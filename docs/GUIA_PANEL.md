# Panel local del Fixture 2030

Abrir http://localhost:8000 con el laboratorio iniciado. Las consultas son de solo lectura y no requieren servicios CDN. Swagger esta en `/docs`.

## Neo4j: explorar todo el conjunto cargado

El endpoint `/api/v1/grafo` devuelve una instantanea del dominio completo del laboratorio: 64 equipos, 1536 jugadores, 96 partidos, 288 eventos y 12 sedes (1996 nodos), con 2400 relaciones. No se reconstruye el grafo a partir de tres eventos: se consultan los nodos y relaciones persistidos.

1. Buscar `AAA`, `Club 1`, `P001` o `Buenos Aires`. La busqueda considera todas las propiedades publicas de todos los nodos cargados, no solo los nombres o resultados visibles en la lista.
2. Elegir un tipo para reducir coincidencias. Cuando hay texto de busqueda, el dibujo incluye tambien los vecinos directos de las coincidencias como contexto.
3. Seleccionar un resultado o un nodo para ver sus propiedades y relaciones dirigidas. Las flechas indican entrada o salida; LOCAL/VISITANTE identifica el rol del equipo.
4. Pulsar una relacion para navegar al nodo conectado, o `Ver conexiones` para aislar su vecindario.
5. Usar `Tabla` para revisar todas las coincidencias; `Restablecer` recupera el grafo entero. `Mas resultados` amplia la lista lateral sin limitar la busqueda.

El contador distingue coincidencias, nodos visibles y nodos cargados. Limites de seguridad: 5000 nodos y 15000 relaciones; `truncado=true` avisa si la instantanea deja de ser completa. No hay ejecucion de Cypher libre ni propiedades de infraestructura/credenciales. Los IDs internos solo identifican nodos dentro de la instantanea actual.

## Las otras bases

- MongoDB: por defecto carga los 64 documentos de equipos del laboratorio. Buscar nombre, codigo, entrenador o confederacion; alternar documentos/tabla y descargar los resultados filtrados. El campo Codigo FIFA permite una consulta directa.
- Cassandra: P001, bloque `2030-06-10T18:00` UTC: 30 comentarios de laboratorio repartidos en los 8 shards segun el resto de dividir el numero de comentario por 8 (shards 0 y 7: 3 comentarios; shards 1 a 6: 4). La busqueda es sobre la particion cargada, no un escaneo global de Cassandra. `Cargar mas` acumula paginas si se elige un limite menor. Otro bloque o shard puede estar vacio.
- Redis: consultar `sess-demo-001`; muestra unicamente estado, ultima actividad y TTL, sin tokens ni informacion privada. La cuenta regresiva es estimada; Consultar comprueba nuevamente Redis. La sesion de muestra vence a los 30 minutos de la carga y un 404 posterior es correcto; consultar no la renueva.
- InfluxDB: P001, desde `2030-06-08T19:00` hasta `2030-06-08T20:30` UTC. Equipo vacio compara todos los equipos devueltos. Elegir posesion, pases, tiros o recuperaciones; la tabla permite inspeccionar todos los campos. Los valores ausentes no se convierten en cero. Si aparece resultado limitado, reducir ventana o aumentar resolucion.
- IRIS: buscar partido por ID, ver propiedades del objeto y sus eventos. La tabla de eventos y el JSON conservan el detalle. La API actual expone partidos y eventos, no todas las clases existentes en cualquier instancia IRIS.

La busqueda local de las vistas no equivale a una consulta sobre registros que la API no ha cargado. No se promete cobertura de colecciones, claves o tablas ajenas a los contratos del Hito 10. La carga de Cassandra es una muestra de laboratorio, no un conjunto original completo.

## Evidencia y reproduccion

La barra muestra estado HTTP, duracion, endpoint y Request ID; `Respuesta JSON` permite cotejar los datos originales de la consulta. Los errores reales se muestran sin sustituirlos por datos ficticios.

```sh
python3 scripts/iniciar_api.py
python3 scripts/ejecutar_pruebas.py
```

La carga Neo4j es idempotente (`MERGE`), conserva los CSV originales y completa equipos, sedes, jugadores y sus relaciones en el laboratorio aislado. No usar el cargador para modificar bases de produccion.
