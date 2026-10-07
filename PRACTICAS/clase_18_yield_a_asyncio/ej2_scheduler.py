#!/usr/bin/env python3
"""Ejercicio 2 (obligatorio): un scheduler cooperativo escrito desde cero.

    --parte a   intercalado de tres tareas, con contador de next()
                (+ una tarea sin ningún yield)
    --parte b   una tarea egoísta que no cede durante 3 segundos
    --parte c   scheduler con tiempo: dormir() sin time.sleep()
    --parte d   qué pasa si se olvida el "yield from" delante de dormir()

Uso:
    python3 ej2_scheduler.py --parte a      (o b, c, d; sin argumento corre todas)
"""
import argparse
import time
from collections import deque

T0 = time.monotonic()


def ahora():
    return f'{time.monotonic() - T0:5.2f}s'


# ---------------------------------------------------------------
# Parte A: intercalar
# ---------------------------------------------------------------

def tarea(nombre, pasos):
    for i in range(1, pasos + 1):
        print(f'  [{ahora()}] [{nombre}] paso {i}/{pasos}')
        yield                        # cedo el control al scheduler
    print(f'  [{ahora()}] [{nombre}] terminada')


def tarea_sin_yield(nombre):
    # Sin yield, esto es una función común: llamarla ejecuta todo de una
    # y devuelve None, no un generador.
    print(f'  [{nombre}] soy una función común')


def scheduler(tareas):
    """Round-robin: saca una tarea, la reanuda y, si no terminó, la reencola."""
    pendientes = deque(tareas)
    llamadas = 0
    while pendientes:
        t = pendientes.popleft()
        try:
            llamadas += 1
            next(t)
            pendientes.append(t)
        except StopIteration:
            pass                     # terminó: no vuelve a la cola
    return llamadas


# ---------------------------------------------------------------
# Parte B: la tarea egoísta
# ---------------------------------------------------------------

def tarea_egoista(nombre):
    print(f'  [{ahora()}] [{nombre}] me pongo a calcular')
    time.sleep(3)                    # no cede el control
    print(f'  [{ahora()}] [{nombre}] listo')
    yield


# ---------------------------------------------------------------
# Parte C: el scheduler entiende de tiempo
# ---------------------------------------------------------------

def dormir(segundos):
    """No duerme: cede informando cuándo quiere que la despierten."""
    yield time.monotonic() + segundos


def tarea_lenta(nombre, veces, espera=0.15):
    for i in range(1, veces + 1):
        print(f'  [{ahora()}] [{nombre}] {i}/{veces}')
        yield from dormir(espera)    # el yield de dormir sube al scheduler
    print(f'  [{ahora()}] [{nombre}] terminada')


def tarea_lenta_sin_yield_from(nombre, veces, espera=0.15):
    for i in range(1, veces + 1):
        print(f'  [{ahora()}] [{nombre}] {i}/{veces}')
        dormir(espera)               # BUG: crea el generador y lo tira
    print(f'  [{ahora()}] [{nombre}] terminada')
    yield                            # (para que siga siendo un generador)


def scheduler_con_tiempo(tareas):
    """Cola de (cuándo_despertar, tarea). Si no hay nadie para correr,
    duerme hasta el próximo despertar (en vez de girar en vacío)."""
    pendientes = deque((0.0, t) for t in tareas)
    while pendientes:
        despertar, t = pendientes.popleft()
        espera = despertar - time.monotonic()
        if espera > 0:
            # ¿Hay alguna otra que ya pueda correr?
            if any(d <= time.monotonic() for d, _ in pendientes):
                pendientes.append((despertar, t))
                continue
            # Nadie listo: el scheduler (no la tarea) duerme lo justo.
            # Es lo que hace un event loop real con el timeout de select().
            proximo = min([despertar] + [d for d, _ in pendientes])
            time.sleep(max(0.0, proximo - time.monotonic()))
            pendientes.appendleft((despertar, t))
            continue
        try:
            cuando = next(t)
            pendientes.append((cuando or 0.0, t))
        except StopIteration:
            pass


# ---------------------------------------------------------------

def parte_a():
    print('=== Parte A: tres tareas intercaladas ===')
    llamadas = scheduler([tarea('A', 3), tarea('B', 2), tarea('C', 4)])
    print(f'  -> next() llamado {llamadas} veces en total')

    print('\n  Tarea sin ningún yield:')
    obj = tarea_sin_yield('X')
    print(f'  tarea_sin_yield() devolvió {obj!r}')
    try:
        scheduler([tarea('A', 1), obj])
    except TypeError as e:
        print(f'  el scheduler falla: TypeError: {e}')


def parte_b():
    print('=== Parte B: una tarea egoísta en el medio ===')
    scheduler([tarea('A', 3), tarea_egoista('EGO'), tarea('C', 3)])


def parte_c():
    print('=== Parte C: tres tareas que esperan 0.15s, cinco corridas ===')
    for corrida in range(1, 6):
        inicio = time.monotonic()
        scheduler_con_tiempo([tarea_lenta('A', 1), tarea_lenta('B', 1),
                              tarea_lenta('C', 1)])
        print(f'  corrida {corrida}: total {time.monotonic() - inicio:.3f}s '
              f'(suma de esperas = 0.45s)\n')

    print('  Con varias esperas por tarea (A:3, B:2, C:4):')
    inicio = time.monotonic()
    scheduler_con_tiempo([tarea_lenta('A', 3), tarea_lenta('B', 2),
                          tarea_lenta('C', 4)])
    print(f'  total {time.monotonic() - inicio:.2f}s (suma de esperas = 1.35s)')


def parte_d():
    print('=== Parte D: sin "yield from" ===')
    inicio = time.monotonic()
    scheduler_con_tiempo([tarea_lenta_sin_yield_from('A', 3),
                          tarea_lenta_sin_yield_from('B', 3)])
    print(f'  total {time.monotonic() - inicio:.3f}s: ¡no esperó nada!')
    print('  dormir(espera) sin yield from solo CREA un generador y lo descarta.')


def main():
    parser = argparse.ArgumentParser(description='Scheduler cooperativo')
    parser.add_argument('--parte', choices='abcd')
    args = parser.parse_args()
    partes = {'a': parte_a, 'b': parte_b, 'c': parte_c, 'd': parte_d}
    for letra in (args.parte or 'abcd'):
        partes[letra]()
        print()


if __name__ == '__main__':
    main()
