#!/usr/bin/env bash
# Ejercicio 5: el límite de socketserver (un thread por conexión).
# Levanta comandos.py, abre 200 y luego 1000 conexiones, y mide threads y
# memoria del proceso servidor. Solo toca procesos que lanza este script.
#
# Uso:  bash comandos.sh [puerto]      (default 8080)
set -u
PUERTO="${1:-8080}"
cd "$(dirname "$0")"

# Servidor en background con timeout largo para que no corte a los ociosos.
python3 comandos.py --port "$PUERTO" --timeout 300 > /dev/null 2>&1 &
SRV=$!
# SIGTERM (no SIGINT): en un script los procesos en background ignoran SIGINT.
trap 'kill $SRV 2>/dev/null; wait $SRV 2>/dev/null' EXIT
sleep 0.5

medir() {
    # Threads: cada entrada de /proc/<pid>/task es un hilo del proceso.
    # Usamos el PID guardado en vez de pgrep, para no medir otro proceso.
    echo "  threads: $(ls /proc/$SRV/task | wc -l)"
    echo "  RSS:     $(ps -o rss= -p $SRV) KB"
}

echo "== Servidor en reposo"
medir

for N in 200 1000; do
    echo "== Con $N conexiones abiertas"
    python3 ej5_conexiones.py -n "$N" --port "$PUERTO" --espera 4 &
    CLI=$!
    sleep 2.5            # tiempo para que se abran todas
    medir
    wait $CLI
    sleep 3            # que terminen los threads de los que se fueron
done

echo "== Después de cerrar todo"
medir
