"""Metricas Prometheus del Hito 10. Sin IDs, contenido de comentarios ni datos personales."""
from prometheus_client import Histogram

BUCKETS = (.001, .0025, .005, .01, .025, .05, .1, .25, .5, 1, 2.5, 5)

HTTP_LATENCY = Histogram("fixture2030_http_request_duration_seconds",
                         "Tiempo de respuesta HTTP de la API, excluye /metrics",
                         ["method", "route", "status"], buckets=BUCKETS)
COMMENT_WRITE = Histogram("fixture2030_comentario_escritura_segundos",
                          "Duracion del LOGGED BATCH que publica un comentario en Cassandra",
                          ["result"], buckets=BUCKETS)
