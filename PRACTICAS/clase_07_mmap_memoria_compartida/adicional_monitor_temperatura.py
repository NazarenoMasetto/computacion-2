#!/usr/bin/env python3
"""
Adicional: monitor de temperatura.
N procesos "sensores" escriben su temperatura en un Array compartido (cada uno en su
posición) y un proceso "monitor" lee periódicamente y muestra promedio, máximo y mínimo.

Uso: python3 adicional_monitor_temperatura.py [num_sensores] [segundos]   (default 4 y 5)
"""
from multiprocessing import Process, Array, Value
import os
import random
import time


def sensor(temperaturas, activo, idx):
    """Simula un sensor: la temperatura hace una caminata aleatoria."""
    random.seed(os.getpid())
    temp = random.uniform(18, 30)
    while activo.value:
        temp += random.uniform(-0.5, 0.5)
        temperaturas[idx] = temp  # cada sensor escribe SOLO su casillero
        time.sleep(random.uniform(0.1, 0.3))


def monitor(temperaturas, activo, intervalo):
    """Lee el array cada 'intervalo' segundos y muestra las estadísticas."""
    while activo.value:
        # Copiamos todo de una vez con el lock del Array para tener una "foto" coherente
        with temperaturas.get_lock():
            foto = temperaturas[:]
        leidas = [t for t in foto if t != 0.0]  # 0.0 = sensor que todavía no escribió
        if leidas:
            prom = sum(leidas) / len(leidas)
            valores = " ".join(f"{t:5.1f}" for t in foto)
            print(f"[MONITOR] [{valores}] prom={prom:5.2f} max={max(leidas):5.2f} "
                  f"min={min(leidas):5.2f}", flush=True)
        time.sleep(intervalo)


def main():
    import sys
    num_sensores = int(sys.argv[1]) if len(sys.argv) > 1 else 4
    duracion = float(sys.argv[2]) if len(sys.argv) > 2 else 5

    temperaturas = Array('d', num_sensores)  # arranca en 0.0
    activo = Value('b', 1)                   # flag compartido para cortar a todos

    procesos = [Process(target=sensor, args=(temperaturas, activo, i))
                for i in range(num_sensores)]
    procesos.append(Process(target=monitor, args=(temperaturas, activo, 0.5)))
    for p in procesos:
        p.start()

    print(f"{num_sensores} sensores + 1 monitor corriendo durante {duracion}s...")
    try:
        time.sleep(duracion)
    except KeyboardInterrupt:
        pass
    activo.value = 0
    for p in procesos:
        p.join()
    print("Sistema detenido")


if __name__ == "__main__":
    main()
