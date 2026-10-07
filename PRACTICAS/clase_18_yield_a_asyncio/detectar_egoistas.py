#!/usr/bin/env python3
"""Adicional: detectar tareas egoístas en el scheduler.

Se mide cuánto tarda cada reanudación (cada next()). Si una tarea tuvo el
control más de UMBRAL segundos sin ceder, se avisa por pantalla. Es lo que
hace asyncio con loop.set_debug(True) y slow_callback_duration (0.1s).

Al final se muestra lo mismo con asyncio real en modo debug.

Uso:
    python3 detectar_egoistas.py [--umbral 0.1]
"""
import argparse
import asyncio
import logging
import time
from collections import deque


def tarea(nombre, pasos):
    for _ in range(pasos):
        yield


def tarea_egoista(nombre, segundos):
    yield
    time.sleep(segundos)             # no cede durante este rato
    yield


def scheduler_vigilante(tareas, umbral):
    pendientes = deque(tareas)
    while pendientes:
        nombre, t = pendientes.popleft()
        inicio = time.perf_counter()
        try:
            next(t)
            terminada = False
        except StopIteration:
            terminada = True
        duracion = time.perf_counter() - inicio
        if duracion > umbral:
            print(f'  AVISO: "{nombre}" tuvo el control {duracion:.3f}s sin ceder '
                  f'(umbral {umbral}s)')
        if not terminada:
            pendientes.append((nombre, t))


async def egoista_async():
    time.sleep(0.3)                  # bloquea el loop


async def main_asyncio():
    asyncio.get_running_loop().set_debug(True)
    await asyncio.gather(asyncio.sleep(0.1), egoista_async())


def main():
    parser = argparse.ArgumentParser(description='Detectar tareas egoístas')
    parser.add_argument('--umbral', type=float, default=0.1)
    args = parser.parse_args()

    print('=== Nuestro scheduler ===')
    scheduler_vigilante([('A', tarea('A', 5)),
                         ('EGO', tarea_egoista('EGO', 0.4)),
                         ('C', tarea('C', 5))], args.umbral)

    print('\n=== asyncio con loop.set_debug(True) ===')
    logging.basicConfig(level=logging.WARNING, format='  asyncio: %(message)s')
    asyncio.run(main_asyncio())


if __name__ == '__main__':
    main()
