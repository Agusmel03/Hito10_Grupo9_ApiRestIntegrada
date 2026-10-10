# Conectividad y configuracion

`python3 scripts/iniciar_api.py` es el punto de entrada. Utiliza dos proyectos
Compose: `fixture2030-hito10` para API y cinco motores, y `hito10-influx` para
InfluxDB. La API participa en ambas redes. No se requiere PowerShell.

| Fuente | Host desde API Docker | Puerto interno | Contexto |
|---|---|---|---|
| MongoDB | mongo | 27017 | fixture2030 |
| Neo4j | neo4j | 7687 | neo4j |
| Cassandra | cassandra | 9042 | fixture2030_comentarios |
| Redis | redis | 6379 | DB 0 |
| InfluxDB | hito10-influxdb | 8086 | grupo9 / estadisticas_live |
| IRIS | iris | 1972 | USER |

Desde la notebook: API `localhost:8000`, InfluxDB `localhost:8086`. Los otros
puertos no se publican. `localhost` dentro del contenedor API es la propia API,
no la notebook ni otro motor. Si se usan fuentes externas, cambiar `.env` con
hosts accesibles desde Docker y no ejecutar scripts de semilla de laboratorio.

`.env.example` documenta las variables; `scripts/configurar.py` genera secretos
aleatorios sin mostrarlos. `.env` se excluye de Git y del contexto de build.
Las credenciales IRIS se aplican solo al nuevo servicio `iris`. El servicio
`iris-permissions` asigna al usuario de IRIS el directorio raiz de su volumen;
no cambia carpetas del equipo ni volumenes de los otros hitos.

Limites de espera (TIMEOUT_SECONDS, 5 segundos por defecto):

- MongoDB: seleccion de servidor, conexion, socket y timeout total del driver.
- Neo4j: conexion, adquisicion y timeout de consulta; sin reintentos automaticos.
- Cassandra: conexion, canal de control y request; politica sin reintentos.
- Redis: conexion y socket; una transaccion corta para leer estado y TTL.
- InfluxDB: timeout del cliente en milisegundos, sin reintentos.
- IRIS: timeout de conexion soportado por el SDK 5.3.2. Ese SDK no ofrece
  `Cursor.setQueryTimeout`; no se promete un limite duro por sentencia SQL.
  Se usan igualdad sobre indice y TOP acotado. Para produccion hace falta
  configurar tambien limites de ejecucion en el servidor.

La duracion total puede incluir mas de una operacion del driver y no equivale
necesariamente al timeout de una sola operacion. Salud consulta en paralelo.

Diagnostico:

```sh
docker compose ps
docker compose -f compose.influx.yml ps
docker compose run --rm api python -m scripts.verificar_conectividad
docker compose logs --tail 50 api
```

La API debe continuar respondiendo si una fuente falla. El estado global sera
503, mientras que rutas de otras fuentes podran seguir devolviendo 200.
No ejecutar `docker compose config` ni `docker inspect` sin filtrar su salida
en evidencias publicas: pueden incluir variables con secretos.

Los volumenes guardan datos entre reinicios. Detener con `stop`, nunca con
`down -v` salvo que se quiera destruir deliberadamente el laboratorio.
El almacenamiento MongoDB del hito anterior con errores de permisos no se
modifica: la integracion usa una muestra equivalente en volumen Docker propio.
