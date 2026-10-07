#!/usr/bin/env python3
"""Tres formas de escribir un endpoint lento, y cuál arruina el servidor.

Levanta una API con tres endpoints que tardan lo mismo pero están
escritos distinto, y les manda pedidos concurrentes para medir.

El resultado es contraintuitivo: un def común anda mejor que un
async def mal escrito.

Agregado (ejercicio 5.7): un cuarto endpoint que hace cálculo pesado
(sha256 iterado), escrito de tres formas para ver cuál conviene:
    /hash-async     async def que calcula directo (bloquea el loop)
    /hash-sync      def común (va al threadpool, pero choca con el GIL)
    /hash-proceso   async def que delega a un ProcessPoolExecutor

Uso:
    pip install fastapi uvicorn httpx
    python3 medir.py              # puerto 8001
    PUERTO=30010 python3 medir.py
"""
import asyncio
import hashlib
import multiprocessing
import os
import time
from concurrent.futures import ProcessPoolExecutor
from contextlib import asynccontextmanager

from fastapi import FastAPI

PUERTO = int(os.environ.get('PUERTO', 8001))
PEDIDOS = 3
DEMORA = 1.0
VUELTAS = int(os.environ.get('VUELTAS', 1_000_000))   # ajustar para ~0.5-1s por hash

@asynccontextmanager
async def ciclo_de_vida(app):
    """Al apagar uvicorn, cerrar el pool de procesos (si no, quedan huérfanos)."""
    yield
    if pool is not None:
        pool.shutdown(cancel_futures=True)


app = FastAPI(lifespan=ciclo_de_vida)


@app.get('/async-bien')
async def async_bien():
    """Corrutina que CEDE el control: el loop atiende a otros mientras."""
    await asyncio.sleep(DEMORA)
    return {'ok': True}


@app.get('/async-mal')
async def async_mal():
    """Corrutina que NO cede: bloquea el event loop y con él a todos."""
    time.sleep(DEMORA)                    # el bug de la clase 18
    return {'ok': True}


@app.get('/sync')
def sincronico():
    """def común: FastAPI lo manda a un threadpool, fuera del loop."""
    time.sleep(DEMORA)
    return {'ok': True}


# ---------------------------------------------------------------
# Cuarto endpoint: cálculo pesado (CPU-bound)
# ---------------------------------------------------------------

def hash_iterado(vueltas=VUELTAS):
    """sha256 aplicado sobre su propio resultado `vueltas` veces."""
    h = b'computacion2'
    for _ in range(vueltas):
        h = hashlib.sha256(h).digest()
    return h.hex()


# El pool de procesos se crea la primera vez que se usa (dentro del proceso
# que corre uvicorn), no al importar el módulo.
pool = None


def obtener_pool():
    global pool
    if pool is None:
        pool = ProcessPoolExecutor(max_workers=os.cpu_count())
    return pool


@app.get('/hash-async')
async def hash_async():
    """MAL: calcula dentro del loop, nadie más es atendido mientras."""
    return {'hash': hash_iterado()}


@app.get('/hash-sync')
def hash_sync():
    """Va al threadpool: no congela el loop, pero los threads se pelean el GIL."""
    return {'hash': hash_iterado()}


@app.get('/hash-proceso')
async def hash_proceso():
    """BIEN: el cálculo va a otro proceso (otro GIL, otro core) y acá se espera con await."""
    loop = asyncio.get_running_loop()
    return {'hash': await loop.run_in_executor(obtener_pool(), hash_iterado)}


def levantar():
    import uvicorn
    uvicorn.run(app, host='127.0.0.1', port=PUERTO, log_level='error')


async def medir(ruta):
    import httpx
    async with httpx.AsyncClient(timeout=30) as cliente:
        t0 = time.perf_counter()
        respuestas = await asyncio.gather(*(
            cliente.get(f'http://127.0.0.1:{PUERTO}/{ruta}')
            for _ in range(PEDIDOS)
        ))
        for r in respuestas:
            r.raise_for_status()          # que un 500 no pase por "rápido"
        return time.perf_counter() - t0


async def correr_mediciones():
    print(f'{PEDIDOS} pedidos concurrentes a endpoints que tardan {DEMORA}s:\n')
    resultados = {}
    for ruta in ('async-bien', 'async-mal', 'sync'):
        resultados[ruta] = await medir(ruta)
        print(f'  /{ruta:<12} {resultados[ruta]:5.2f}s')

    print(f'\n  /async-bien  se solapan: el await cede el control.')
    print(f'  /async-mal   NO se solapan: time.sleep bloquea el event loop,')
    print(f'               y como es uno solo, congela todos los pedidos.')
    print(f'  /sync        se solapan igual que el primero: FastAPI detecta')
    print(f'               que no es corrutina y lo manda a un threadpool.')
    print(f'\n  Conclusión: un def común es MEJOR que un async def mal escrito.')
    print(f'  Si tu función bloquea y no hay alternativa async, usá def.')

    # --- cuarto endpoint: CPU ---
    t0 = time.perf_counter()
    hash_iterado()
    uno = time.perf_counter() - t0
    print(f'\n{PEDIDOS} pedidos concurrentes a un hash iterado '
          f'(uno solo tarda {uno:.2f}s acá, {os.cpu_count()} cores):\n')
    for ruta in ('hash-async', 'hash-sync', 'hash-proceso'):
        dt = await medir(ruta)
        print(f'  /{ruta:<13} {dt:5.2f}s')
    print(f'\n  /hash-async   serializa todo y además congela el loop.')
    print(f'  /hash-sync    no congela el loop, pero el GIL deja correr un')
    print(f'                thread de Python a la vez: tarda casi lo mismo.')
    print(f'  /hash-proceso reparte entre cores: lo único que escala con CPU.')


def main():
    # No daemon: un proceso daemon no puede tener hijos, y el
    # ProcessPoolExecutor de /hash-proceso los necesita.
    servidor = multiprocessing.Process(target=levantar)
    servidor.start()
    time.sleep(3)                          # esperar a que levante
    try:
        asyncio.run(correr_mediciones())
    finally:
        servidor.terminate()
        servidor.join(timeout=5)


if __name__ == '__main__':
    main()
