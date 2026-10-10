"""Reproduce the original Hito 8 sample using the configured InfluxDB 2 instance."""
from pathlib import Path
import runpy

from influxdb_client import InfluxDBClient, BucketRetentionRules
from influxdb_client.client.write_api import SYNCHRONOUS

from app.config.settings import Settings


def main():
    s = Settings()
    if s.influx_url != "http://hito10-influxdb:8086" or s.influx_org != "grupo9":
        raise SystemExit("Solo se permite sembrar la instancia InfluxDB de laboratorio.")
    generator = runpy.run_path("data/influx/generacion_puntos_original.py")
    points = [line for match in generator["PARTIDOS"] for line in generator["generar_partido"](match)]
    with InfluxDBClient(url=s.influx_url, token=s.influx_token.get_secret_value(), org=s.influx_org, timeout=10000) as client:
        buckets = client.buckets_api()
        for name, seconds in [("estadisticas_historicas", 365*86400), ("estadisticas_benchmark", 86400)]:
            if buckets.find_bucket_by_name(name) is None:
                buckets.create_bucket(bucket_name=name, org=s.influx_org,
                                      retention_rules=BucketRetentionRules(type="expire", every_seconds=seconds))
        with client.write_api(write_options=SYNCHRONOUS) as writer:
            writer.write(bucket=s.influx_bucket, record="\n".join(points), write_precision="ms")
        client.query_api().query(Path("data/influx/downsampling.flux").read_text())
        for bucket, measurement, expected in [(s.influx_bucket, "estadisticas_equipo", 8640),
                ("estadisticas_historicas", "estadisticas_equipo_resumen_1m", 720)]:
            tables = client.query_api().query(f'''from(bucket: "{bucket}")
                |> range(start: 2030-06-08T18:59:00Z, stop: 2030-06-08T21:00:00Z)
                |> filter(fn: (r) => r._measurement == "{measurement}" and r._field == "posesion_pct")
                |> group() |> count()''')
            count = sum(record.get_value() for table in tables for record in table.records)
            if count != expected:
                raise RuntimeError(f"{bucket}: se esperaban {expected}; encontrados {count}")
            print(f"InfluxDB: {bucket}, {count} puntos verificados.")


if __name__ == "__main__":
    main()
