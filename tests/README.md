# Pruebas reproducibles

Desde el host, con el laboratorio iniciado:

```sh
python3 scripts/ejecutar_pruebas.py
```

Solo pruebas unitarias, sin consultas a las bases:

```sh
docker compose run --rm --no-deps api python -m pytest tests/unit -q
```

Integracion real:

```sh
docker compose run --rm --no-deps -e RUN_INTEGRATION=1 api python -m pytest tests/integration -q
```

La muestra debe cargarse antes de las pruebas. Redis tiene TTL de 1800 segundos;
si vencio, volver a ejecutar `scripts.sembrar_lab` como se explica en README.
Una prueba de expiracion crea una clave de laboratorio con TTL de un segundo
y la elimina al terminar. No realiza escrituras en Redis externos.

Cobertura: una lectura exitosa por motor y esquema de respuesta, validacion
antes de consultar, ausencia, lista vacia, paginacion MongoDB/Cassandra,
cursor alterado/expirado/de otra particion, correlacion y errores sin secretos,
sesion expirada, agregaciones temporales y las seis dependencias inaccesibles.
Las pruebas de dependencia utilizan un puerto local cerrado, no un mock, con
limite de duracion. No requiere detener una base del usuario.

`scripts/verificar_conectividad.py` verifica ademas la API HTTP en ejecucion,
captura requests, respuestas, latencias e IDs en `docs/evidencia/` y termina
con error si una expectativa no se cumple. No se deben presentar pruebas
omitidas como aprobadas ni reemplazar errores por respuestas ficticias.
