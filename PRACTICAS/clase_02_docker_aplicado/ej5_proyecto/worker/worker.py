"""Worker del proyecto integrador.

Proceso en background que cada INTERVALO segundos incrementa un contador
en Redis y guarda la hora del último incremento.

Variables de entorno:
    REDIS_HOST  host de Redis (default: localhost)
    INTERVALO   segundos entre incrementos (default: 1)
"""

import os
import signal
import sys
import time
from datetime import datetime

import redis

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
INTERVALO = float(os.getenv("INTERVALO", "1"))


def terminar(signum, frame):
    # docker stop manda SIGTERM: salimos prolijamente
    print("Worker: recibí SIGTERM, termino.", flush=True)
    sys.exit(0)


def conectar():
    """Reintenta hasta que Redis esté listo (depends_on no espera a que arranque)."""
    r = redis.Redis(host=REDIS_HOST, port=6379, decode_responses=True)
    for intento in range(1, 31):
        try:
            r.ping()
            return r
        except redis.ConnectionError:
            print(f"Worker: Redis no responde (intento {intento}), reintento...", flush=True)
            time.sleep(1)
    print("Worker: no pude conectar a Redis", flush=True)
    sys.exit(1)


def main():
    signal.signal(signal.SIGTERM, terminar)
    r = conectar()
    print(f"Worker: conectado a Redis en {REDIS_HOST}", flush=True)
    while True:
        valor = r.incr("contador")
        r.set("worker_ultimo", datetime.now().isoformat(timespec="seconds"))
        print(f"Worker: contador = {valor}", flush=True)
        time.sleep(INTERVALO)


if __name__ == "__main__":
    main()
