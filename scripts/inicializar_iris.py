"""Run on the host with Docker; initialize only this Compose IRIS service."""
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parent.parent
commands = '''zn "%SYS"
set properties("Password")=$SYSTEM.Util.GetEnviron("IRIS_LAB_PASSWORD")
set properties("ChangePassword")=0
set sc=##class(Security.Users).Modify("_SYSTEM",.properties)
if $SYSTEM.Status.IsError(sc) do $SYSTEM.Status.DisplayError(sc) halt 1
zn "USER"
set sc=$SYSTEM.OBJ.Load("/src/Persona.cls","ck")
if $SYSTEM.Status.IsError(sc) do $SYSTEM.Status.DisplayError(sc) halt 1
set sc=$SYSTEM.OBJ.Load("/src/Jugador.cls","ck")
if $SYSTEM.Status.IsError(sc) do $SYSTEM.Status.DisplayError(sc) halt 1
set sc=$SYSTEM.OBJ.Load("/src/Arbitro.cls","ck")
if $SYSTEM.Status.IsError(sc) do $SYSTEM.Status.DisplayError(sc) halt 1
set sc=$SYSTEM.OBJ.Load("/src/Partido.cls","u")
if $SYSTEM.Status.IsError(sc) do $SYSTEM.Status.DisplayError(sc) halt 1
set sc=$SYSTEM.OBJ.Load("/src/Evento.cls","ck")
if $SYSTEM.Status.IsError(sc) do $SYSTEM.Status.DisplayError(sc) halt 1
set sc=$SYSTEM.OBJ.Compile("Fixture2030.Partido","ck")
if $SYSTEM.Status.IsError(sc) do $SYSTEM.Status.DisplayError(sc) halt 1
set sc=$SYSTEM.OBJ.Load("/src/CargaObjetos.cls","ck")
if $SYSTEM.Status.IsError(sc) do $SYSTEM.Status.DisplayError(sc) halt 1
set sc=##class(Fixture2030.CargaObjetos).Ejecutar()
if $SYSTEM.Status.IsError(sc) do $SYSTEM.Status.DisplayError(sc) halt 1
write "HITO10_IRIS_OK",!
halt
'''
result = subprocess.run(["docker", "compose", "exec", "-T", "iris", "iris", "session", "IRIS"],
                        input=commands, text=True, capture_output=True, cwd=ROOT, timeout=90)
# Never echo the session: interactive command echoes may contain configuration.
if result.returncode or "HITO10_IRIS_OK\r\n" not in result.stdout and "HITO10_IRIS_OK\n" not in result.stdout:
    print("No se pudo completar la inicializacion de IRIS. Revisar clases y disponibilidad.")
    raise SystemExit(1)
print("Clases Fixture2030 cargadas y partido P001 persistido en IRIS de laboratorio.")
