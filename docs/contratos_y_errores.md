# Contratos, validacion e idempotencia

OpenAPI 3.1 se genera de las rutas y modelos en tiempo de ejecucion y se exporta
a `openapi/openapi.yaml`. Swagger y Postman utilizan las mismas rutas.

Respuesta exitosa: `{"data": ...}`. Respuesta de error:

```json
{"error":{"code":"dependencia_no_disponible","message":"No se pudo consultar la fuente de datos.","request_id":"bc867f9c-bc84-456c-b333-f90e4e75d2e6","dependency":"redis","fields":[]}}
```

| HTTP | Significado |
|---|---|
| 200 | Lectura valida, incluso lista vacia cuando corresponde |
| 404 | Equipo, partido u objeto ausente; sesion no vigente |
| 422 | Formato, limite, fecha, ventana, shard o cursor invalido |
| 503 | Fuente inaccesible, error del driver o timeout |
| 500 | Error inesperado, respuesta publica sin detalle sensible |

`/api/v1/salud` es una excepcion documentada al esquema de error: usa el mismo
objeto de estado por fuente tanto con 200 como con 503 (estado degradado).
`/health/live` solo verifica el proceso; no afirma que las bases esten disponibles.
No hay 409 porque no se implementan escrituras ni conflictos de transicion.

Reglas de entrada y limites:

- Codigo FIFA: exactamente tres letras mayusculas. Partido: P y 3 a 9 digitos.
- MongoDB: limite 1..100; filtro de confederacion enumerado; siguiente_codigo
  permite continuar con `despues`. Indices unico por codigo y compuesto por filtro.
- Neo4j: limite 1..100, offset 0..10000; orden por minuto, evento y jugador.
  Partido inexistente es 404; partido sin eventos devuelve items vacio.
- Cassandra: bucket UTC alineado a diez minutos, shard 0..7, limite 1..100.
  Cursor firmado de hasta 8192 caracteres, ligado a parametros y valido una hora.
  Sin resultados no se puede inferir si el partido existe en otro motor.
- Redis: ID alfanumerico con guion/guion bajo, maximo 80 caracteres. Solo se
  consideran vigentes hashes activos con TTL no negativo. No se expone usuario.
- InfluxDB: fechas con zona horaria, desde < hasta, maximo 24 horas;
  resolucion 1m, 5m, 15m o 1h. Promedio para posesion; ultimo valor para pases;
  suma para tiros y recuperaciones. Hasta 1000 puntos, con indicador truncado.
  Reducir intervalo o aumentar resolucion si truncado es true.
- IRIS: limite de eventos 1..100; indicador eventos_truncados. Fecha conserva
  el timestamp local del hito sin inventar un huso horario.

InfluxDB usa un intervalo semiabierto [desde,hasta). El tiempo de una agregacion
representa el final de su ventana; una ventana parcial puede etiquetarse despues
de hasta. Ausencia de puntos es 200; fallo de conexion nunca se convierte en [].

Todos los GET son idempotentes: no escriben, no renuevan TTL y no invalidan cache.
Las paginas no constituyen un snapshot frente a escrituras externas concurrentes.
La clave de firma de cursores se conserva en `.env`; cambiarla invalida cursores.
Los scripts de semilla utilizan IDs estables y upsert/MERGE; Redis renueva
explicitamente la sesion de laboratorio. La carga inicial de Cassandra escribe
ambas tablas, pero no se presenta como una transaccion distribuida de negocio.
