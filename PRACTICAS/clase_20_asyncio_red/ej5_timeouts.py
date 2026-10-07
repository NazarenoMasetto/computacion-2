#!/usr/bin/env python3
"""Ejercicio 5: timeouts y cancelación.

    5.1  asyncio.timeout: qué lanza y qué le pasa a la operación;
         comparación con asyncio.wait_for
    5.2  cancelar una corrutina que calcula sin await (punto 6)
         y tragarse el CancelledError sin relanzarlo (punto 7)

Uso:
    python3 ej5_timeouts.py            # el cálculo sin await dura 5 s
    SEGUNDOS=2 python3 ej5_timeouts.py
"""
import asyncio
import os
import time

SEGUNDOS = float(os.environ.get('SEGUNDOS', 5))


async def operacion_lenta(nombre):
    try:
        await asyncio.sleep(10)
        print(f'  [{nombre}] terminó (no debería)')
    except asyncio.CancelledError:
        print(f'  [{nombre}] recibió CancelledError: la cancelaron')
        raise
    finally:
        print(f'  [{nombre}] finally')


async def con_timeout():
    print('5.1 asyncio.timeout(2) sobre una operación de 10 s')
    t0 = time.perf_counter()
    try:
        async with asyncio.timeout(2):
            await operacion_lenta('timeout')
    except TimeoutError as e:
        print(f'  afuera llega {type(e).__module__}.{type(e).__name__} '
              f'a los {time.perf_counter() - t0:.2f}s')
        print(f'  ¿es asyncio.TimeoutError? {type(e) is asyncio.TimeoutError}')

    print('\n    asyncio.wait_for(..., 2) sobre lo mismo')
    t0 = time.perf_counter()
    try:
        await asyncio.wait_for(operacion_lenta('wait_for'), 2)
    except TimeoutError as e:
        print(f'  afuera llega {type(e).__name__} a los {time.perf_counter() - t0:.2f}s')


def calcular(segundos):
    """CPU puro: no hay ningún punto donde ceder el control."""
    fin = time.perf_counter() + segundos
    n = 0
    while time.perf_counter() < fin:
        n += 1
    return n


async def sin_await():
    calcular(SEGUNDOS)
    return 'terminé el cálculo'


async def cancelar_sin_await():
    print(f'\n5.2.6 cancelar a los 0.5 s una corrutina que calcula {SEGUNDOS:.0f} s sin await')
    t0 = time.perf_counter()
    tarea = asyncio.create_task(sin_await())

    async def cancelador():
        await asyncio.sleep(0.5)
        print(f'  cancelador: llamo a cancel() a los {time.perf_counter() - t0:.2f}s')
        tarea.cancel()

    otra = asyncio.create_task(cancelador())
    try:
        resultado = await tarea
        print(f'  la tarea devolvió {resultado!r} a los {time.perf_counter() - t0:.2f}s')
    except asyncio.CancelledError:
        print(f'  CancelledError recién a los {time.perf_counter() - t0:.2f}s')
    await otra
    print(f'  tarea.cancelled() = {tarea.cancelled()}: el cancel() llegó tarde')

    print('\n    con asyncio.timeout(0.5) alrededor:')
    t0 = time.perf_counter()
    try:
        async with asyncio.timeout(0.5):
            resultado = await sin_await()
        print(f'  sin TimeoutError: devolvió {resultado!r} a los '
              f'{time.perf_counter() - t0:.2f}s')
    except TimeoutError:
        print(f'  TimeoutError recién a los {time.perf_counter() - t0:.2f}s')


async def traga_cancelacion():
    """MAL: atrapa CancelledError y sigue como si nada."""
    for i in range(3):
        try:
            await asyncio.sleep(0.3)
        except asyncio.CancelledError:
            print('  [tragona] me cancelaron... y lo ignoro')
    return 'terminé igual'


async def tragar_cancelled():
    print('\n5.2.7 capturar CancelledError y no relanzarla')
    tarea = asyncio.create_task(traga_cancelacion())
    await asyncio.sleep(0.1)
    tarea.cancel()
    resultado = await tarea
    print(f'  quien canceló recibe {resultado!r}; tarea.cancelled() = {tarea.cancelled()}')

    t0 = time.perf_counter()
    try:
        async with asyncio.timeout(0.1):
            print('  con asyncio.timeout(0.1):', await traga_cancelacion())
    except TimeoutError:
        print('  TimeoutError')
    print(f'  el "timeout de 0.1 s" duró {time.perf_counter() - t0:.2f}s')


async def main():
    await con_timeout()
    await cancelar_sin_await()
    await tragar_cancelled()
    print('\nCancelledError hereda de:', asyncio.CancelledError.__mro__[1].__name__)


if __name__ == '__main__':
    asyncio.run(main())
