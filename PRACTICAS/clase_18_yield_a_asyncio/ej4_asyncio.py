#!/usr/bin/env python3
"""Ejercicio 4: asyncio de verdad.

    4.1  el scheduler de la parte A con asyncio (y los errores del 4.1.2/3)
    4.2  crear una corrutina no es ejecutarla
    4.3  gather: orden de finalización, orden de resultados y comparación
         contra await en secuencia

Uso:
    python3 ej4_asyncio.py
"""
import asyncio
import gc
import time
import warnings


# ---------------------------------------------------------------
# 4.1 El equivalente al scheduler
# ---------------------------------------------------------------

async def tarea(nombre, pasos):
    for i in range(1, pasos + 1):
        print(f'  [{nombre}] paso {i}/{pasos}')
        await asyncio.sleep(0)          # equivale al "yield" de nuestro scheduler
    print(f'  [{nombre}] terminada')
    return nombre


async def main_41():
    resultados = await asyncio.gather(tarea('A', 3), tarea('B', 2), tarea('C', 4))
    print(f'  gather devolvió {resultados}')


async def main_sin_await():
    # Sin await: gather programa las tareas pero main termina enseguida
    futuro = asyncio.gather(tarea('A', 2), tarea('B', 2))
    print(f'  sin await, gather devuelve: {type(futuro).__name__}')
    # al salir, asyncio.run() cancela lo pendiente


async def main_run_adentro():
    try:
        asyncio.run(asyncio.sleep(0))
    except RuntimeError as e:
        print(f'  asyncio.run() adentro de una corrutina: RuntimeError: {e}')


# ---------------------------------------------------------------
# 4.2 Crear no es ejecutar
# ---------------------------------------------------------------

async def saludar():
    print('  hola')


# ---------------------------------------------------------------
# 4.3 gather
# ---------------------------------------------------------------

async def dormir_y_avisar(nombre, segundos):
    await asyncio.sleep(segundos)
    print(f'  terminó {nombre} ({segundos}s)')
    return nombre


async def un_segundo(nombre):
    await asyncio.sleep(1)
    return nombre


async def main_43():
    resultados = await asyncio.gather(dormir_y_avisar('a', 0.3),
                                      dormir_y_avisar('b', 0.1),
                                      dormir_y_avisar('c', 0.2))
    print(f'  gather devolvió: {resultados}  (orden de los argumentos)')

    t0 = time.perf_counter()
    await asyncio.gather(un_segundo('a'), un_segundo('b'), un_segundo('c'))
    print(f'  gather(a(), b(), c()):            {time.perf_counter() - t0:.2f}s')

    t0 = time.perf_counter()
    for nombre in ('a', 'b', 'c'):
        await un_segundo(nombre)
    print(f'  for f in (a, b, c): await f():    {time.perf_counter() - t0:.2f}s')


def main():
    print('=== 4.1 el scheduler con asyncio ===')
    asyncio.run(main_41())

    print('\n=== 4.1.2 olvidar el await delante de gather ===')
    asyncio.run(main_sin_await())

    print('\n=== 4.1.3 asyncio.run() dos veces seguidas ===')
    print('  primera:', asyncio.run(asyncio.sleep(0, result='ok 1')))
    print('  segunda:', asyncio.run(asyncio.sleep(0, result='ok 2')))
    asyncio.run(main_run_adentro())

    print('\n=== 4.2 crear no es ejecutar ===')
    with warnings.catch_warnings(record=True) as avisos:
        warnings.simplefilter('always')
        saludar()                         # no imprime nada
        gc.collect()                      # forzar que se destruya la corrutina
    for w in avisos:
        print(f'  aviso: {w.category.__name__}: {w.message}')
    print('  y ahora con asyncio.run(saludar()):')
    asyncio.run(saludar())

    print('\n=== 4.3 gather ===')
    asyncio.run(main_43())


if __name__ == '__main__':
    main()
