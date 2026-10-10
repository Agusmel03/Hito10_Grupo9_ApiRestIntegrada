# Pruebas y evidencia

Procedimiento: `python3 scripts/iniciar_api.py`, seguido de
`python3 scripts/ejecutar_pruebas.py`. El primer comando carga los datos
deterministas y renueva la sesion de laboratorio. El segundo prueba el codigo
y luego consulta el servicio HTTP que esta corriendo.

Archivos de evidencia generados, no respuestas escritas a mano:

- `evidencia/pytest.xml`: resultados JUnit de pruebas unitarias e integracion.
- `evidencia/http_verificacion.json`: fecha UTC, metodo, entorno, parametros,
  respuestas reales, duracion e identificadores de request por caso.
- `evidencia/correlacion.json`: logs de aplicacion/adaptador correspondientes a
  los IDs de las requests del informe HTTP.

Escenarios: lectura por cada una de las seis fuentes; entradas invalidas sin
llamar a adaptadores; recursos inexistentes; conjuntos vacios validos;
expiracion Redis real; paginacion MongoDB y Cassandra; firma y vencimiento
de cursor; agregaciones InfluxDB; relacion padre-hijo y limite IRIS;
las seis dependencias inaccesibles mediante puerto cerrado y tiempo acotado;
contratos de respuestas y coincidencia del OpenAPI exportado.

Los tests unitarios usan dobles controlados; los de integracion se conectan
a motores Docker reales. Las pruebas sin RUN_INTEGRATION=1 omiten integracion
y no equivalen a una verificacion completa. El informe HTTP exige salud global
200 y expectativas satisfechas; termina con codigo distinto de cero si falla.

La prueba IRIS permitio detectar una incompatibilidad concreta: el SDK 5.3.2
no implementa Cursor.setQueryTimeout. Se retiro esa llamada y se conserva el
timeout de conexion admitido por el driver; ver limitaciones en configuracion.

Rendimiento: el informe mide una request secuencial por caso, sin calentamiento
ni carga concurrente, incluyendo HTTP y acceso a la base. Datos: 64 equipos,
30 comentarios por particion de muestra, 8640 puntos InfluxDB y 720 resumenes,
ademas de partidos/eventos originales y un objeto IRIS con dos hijos.
El laboratorio usa Docker Desktop ARM64, 8 CPU y aproximadamente 4 GB asignados.
Las cifras son observaciones de este entorno, no capacidad maxima ni garantias
para millones de usuarios. Los timestamps de los datos representan 2030;
los timestamps de la evidencia son los de la ejecucion real.

Cobertura de la consigna: casos de uso y lectura de seis fuentes (RF1-RF8),
capas y validacion (RF9-RF10), errores seguros (RF11-RF12), contrato y
coleccion (RF13-RF14), pruebas/configuracion/evidencia (RF15-RF18),
idempotencia de lectura documentada (RF19). RF20 requiere publicar el
contenido en GitHub y otorgar acceso al docente; no lo prueba un test local.
