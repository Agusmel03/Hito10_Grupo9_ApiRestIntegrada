"""Create local configuration without printing or overwriting secrets."""
import os
from pathlib import Path
import secrets
from dotenv import dotenv_values


def main():
    target = Path(".env")
    if target.exists():
        print(".env ya existe; no se modifica.")
        return
    values = dict(dotenv_values(".env.example"))
    previous = dotenv_values("influxdb-hito8/.env")
    values.update(CURSOR_SECRET=secrets.token_hex(32), NEO4J_PASSWORD=secrets.token_urlsafe(24),
                  IRIS_PASSWORD=secrets.token_urlsafe(24),
                  INFLUX_TOKEN=previous.get("INFLUXDB_TOKEN") or secrets.token_urlsafe(48),
                  INFLUX_USERNAME=previous.get("INFLUXDB_USERNAME") or "admin",
                  INFLUX_PASSWORD=previous.get("INFLUXDB_PASSWORD") or secrets.token_urlsafe(24))
    fd = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w") as handle:
        for key, value in values.items():
            handle.write(f"{key}={value or ''}\n")
    print(".env creado con credenciales locales; secretos no impresos.")


if __name__ == "__main__":
    main()
