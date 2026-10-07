#!/usr/bin/env python3
"""
Adicional: monitor de sistema simple. 3 threads daemon imprimen métricas
simuladas (CPU, memoria, disco) cada N segundos; el principal duerme y termina,
llevándose a los daemons.

Uso: python3 ej11_monitor_sistema.py [duracion_principal=10] [intervalo=2]
"""
import random
import sys
import threading
import time


def monitor(metrica, unidad, intervalo, minimo, maximo):
    """Loop infinito: nunca termina solo, por eso tiene que ser daemon."""
    while True:
        valor = random.uniform(minimo, maximo)
        print(f"[{time.strftime('%H:%M:%S')}] {metrica:<8} {valor:6.1f} {unidad}", flush=True)
        time.sleep(intervalo)


if __name__ == "__main__":
    duracion = float(sys.argv[1]) if len(sys.argv) > 1 else 10
    intervalo = float(sys.argv[2]) if len(sys.argv) > 2 else 2

    metricas = [("CPU", "%", 0, 100), ("Memoria", "MB", 500, 8000), ("Disco", "%", 40, 90)]
    for nombre, unidad, mn, mx in metricas:
        threading.Thread(target=monitor, args=(nombre, unidad, intervalo, mn, mx),
                         name=f"mon-{nombre}", daemon=True).start()

    time.sleep(duracion)
    print(f"Principal: pasaron {duracion}s, termino (los daemons mueren conmigo)")
