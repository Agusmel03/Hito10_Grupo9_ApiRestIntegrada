"""Configure only the new isolated IRIS lab; leave old containers untouched."""
import secrets
from dotenv import dotenv_values, set_key

values = dotenv_values(".env")
if not values.get("IRIS_PASSWORD"):
    set_key(".env", "IRIS_PASSWORD", secrets.token_urlsafe(24))
set_key(".env", "IRIS_HOST", "iris")
print("IRIS de laboratorio configurado; credenciales no impresas.")
