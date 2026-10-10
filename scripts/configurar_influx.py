"""Migrate this workspace's earlier Influx setup without exposing its credentials."""
import secrets
from dotenv import dotenv_values, set_key

current = dotenv_values(".env")
previous = dotenv_values("influxdb-hito8/.env")
for target, source, fallback in [
    ("INFLUX_USERNAME", "INFLUXDB_USERNAME", "admin"),
    ("INFLUX_PASSWORD", "INFLUXDB_PASSWORD", secrets.token_urlsafe(24)),
    ("INFLUX_TOKEN", "INFLUXDB_TOKEN", secrets.token_urlsafe(48)),
]:
    if not current.get(target):
        set_key(".env", target, previous.get(source) or fallback)
print("Configuracion InfluxDB lista; secretos no impresos.")
