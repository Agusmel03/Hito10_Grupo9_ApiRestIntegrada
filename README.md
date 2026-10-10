# Fixture 2030 - Hito 10 - Grupo 9

Repositorio: https://github.com/FacuIria/Hito10_Grupo9_ApiRestIntegrada

API REST de lectura con FastAPI y seis adaptadores: MongoDB, Neo4j,
Cassandra, Redis, InfluxDB 2 e InterSystems IRIS. Incluye datos sinteticos,
contrato OpenAPI, Postman, pruebas unitarias y pruebas contra motores reales.

## Inicio reproducible

Requisitos: Docker Desktop iniciado, Docker Compose v2, Python 3.9 o superior
en el equipo anfitrion y acceso a Internet para la primera descarga.
La API utiliza Python 3.11 dentro de Docker; no requiere instalar drivers en la Mac.
El laboratorio se verifico en macOS ARM64 con 4 GB asignados a Docker.
Dejar memoria disponible y detener laboratorios ajenos que no se usen.

Desde la carpeta del proyecto:

```sh
python3 scripts/iniciar_api.py
python3 scripts/ejecutar_pruebas.py
```

El primer comando construye la imagen, genera `.env` con secretos aleatorios
si no existe, inicia las seis bases, carga muestras y abre el servicio HTTP.
No depende de los repositorios externos ni de `influxdb-hito8/`: los datos y
clases necesarios estan incluidos en `data/`. Si esa carpeta anterior existe,
se aprovechan sus credenciales InfluxDB para conservar el entorno previo.

- Interfaz de consultas: http://localhost:8000
- Swagger: http://localhost:8000/docs
- Contrato HTTP: http://localhost:8000/openapi.json
- Estado de las seis fuentes: http://localhost:8000/api/v1/salud
- Proceso HTTP: http://localhost:8000/health/live
- Interfaz InfluxDB: http://localhost:8086 (credenciales en `.env`).

Si el puerto 8000 esta ocupado, definir `API_PORT=8001` en `.env` antes de
iniciar. Swagger utiliza el puerto de la instancia abierta; modificar la
variable `base_url` de Postman. El puerto 8086 debe estar disponible para
InfluxDB o ajustarse en `compose.influx.yml`.

## Recursos

| Metodo | Ruta | Fuente |
|---|---|---|
| GET | `/api/v1/equipos` | MongoDB |
| GET | `/api/v1/equipos/{codigo}` | MongoDB |
| GET | `/api/v1/partidos/{partido_id}/eventos` | Neo4j |
| GET | `/api/v1/partidos/{partido_id}/comentarios` | Cassandra |
| GET | `/api/v1/sesiones/{session_id}` | Redis |
| GET | `/api/v1/partidos/{partido_id}/estadisticas` | InfluxDB |
| GET | `/api/v1/objetos/partidos/{partido_id}` | IRIS |

Ejemplos reproducibles:

```sh
curl -i http://localhost:8000/api/v1/equipos/AAA
curl -i 'http://localhost:8000/api/v1/partidos/P001/comentarios?bucket_10m=2030-06-10T18:00:00Z&shard=0&limite=7'
curl -i 'http://localhost:8000/api/v1/partidos/P001/estadisticas?desde=2030-06-08T19:00:00Z&hasta=2030-06-08T20:30:00Z&resolucion=5m'
curl -i http://localhost:8000/api/v1/objetos/partidos/P001
curl -i http://localhost:8000/api/v1/equipos/aa
curl -i http://localhost:8000/api/v1/equipos/ZZZ
```

Importar `postman/fixture2030_collection.json` en Postman y ejecutar la
coleccion. La sesion `sess-demo-001` vence a los 30 minutos: para renovar solo
los datos de laboratorio ejecutar `docker compose run --rm api python -m scripts.sembrar_lab`.
Los GET nunca renuevan sesiones. Los datos temporales son de junio de 2030:
en InfluxDB elegir ese intervalo absoluto, no "ultima hora".

## Operacion

```sh
docker compose ps
docker compose logs --tail 50 api
docker compose --profile lab stop
docker compose -f compose.influx.yml stop
```

Volver a iniciar con `python3 scripts/iniciar_api.py`. Los volumenes persisten;
la carga usa identificadores estables y no duplica la muestra. No ejecutar
`down -v` para detener: elimina los datos. Los contenedores anteriores de otros
hitos no se usan ni se borran; este proyecto utiliza volumenes propios.

## Documentacion y entrega

- [Casos de uso](docs/casos_de_uso.md)
- [Arquitectura y adaptadores](docs/arquitectura_y_adaptadores.md)
- [Contratos y errores](docs/contratos_y_errores.md)
- [Conectividad y configuracion](docs/conectividad_y_configuracion.md)
- [Pruebas y evidencia](docs/pruebas_y_evidencia.md)
- [Procedencia de las muestras](data/README.md)
- [Pruebas](tests/README.md)

`openapi/openapi.yaml` se genera desde el codigo: no editarlo manualmente.
Regenerar junto con Postman mediante:

```sh
docker compose run --rm api python -m scripts.exportar_contratos
```

Alcance: lecturas idempotentes sobre las seis fuentes; no hay operaciones de
escritura HTTP ni transiciones de estado. Los scripts de carga son herramientas
del laboratorio. No se ofrecen autenticacion de consumidores, alta disponibilidad,
consistencia distribuida ni garantias de produccion. La API se publica solo en
localhost. Los motores sin autenticacion estan limitados a la red Docker local.

## Trabajo en equipo

```sh
git clone https://github.com/FacuIria/Hito10_Grupo9_ApiRestIntegrada.git
cd Hito10_Grupo9_ApiRestIntegrada
python3 scripts/iniciar_api.py
python3 scripts/ejecutar_pruebas.py
git switch -c mejora/nombre-del-cambio
```

Cada integrante genera sus propias credenciales locales al iniciar. No hace
falta compartir `.env`. Para proponer cambios, trabajar en una rama, ejecutar
las pruebas y abrir un pull request hacia `main`. Si cambian las rutas o modelos,
regenerar OpenAPI y Postman antes de ejecutar las pruebas.

Nunca agregar `.env`, tokens ni volcados privados. El propietario debe otorgar
acceso de colaboracion a los integrantes y acceso al docente segun la consigna.
# Vistas por base de datos

El panel en `http://localhost:8000` consulta la API real, en modo solo lectura:

- MongoDB: documentos de equipos y paginacion por codigo FIFA.
- Neo4j: grafo interactivo del partido, eventos y jugadores de la pagina consultada. Las relaciones `OCURRE_EN` y `PROTAGONIZADO_POR` corresponden a la consulta del adaptador; no representa todo el grafo de la base. Seleccion de nodos, propiedades, zoom y ajuste de vista.
- Cassandra: comentarios con su particion (partido, bloque UTC y shard) y cursor.
- Redis: estado de sesion y TTL observado, con cuenta regresiva estimada localmente. Una sesion vencida requiere una nueva consulta para confirmar su estado.
- InfluxDB: curvas por equipo y selector de metrica, respetando valores ausentes.
- IRIS: propiedades del objeto partido y sus eventos asociados.

Las bibliotecas visuales y sus licencias estan en `app/frontend/vendor`; el navegador no necesita acceder a un CDN. Los errores de las bases se muestran sin sustituirlos por datos ficticios.
