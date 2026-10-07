#!/usr/bin/env python3
"""Ejercicio 5.5 y 5.6: el endpoint /datos mal escrito y dos arreglos.

    /datos-mal     async def + requests      -> bloquea el event loop
    /datos-def     def + requests            -> arreglo 1: cambiar el async def
    /datos-httpx   async def + httpx async   -> arreglo 2: cambiar la biblioteca

Como no hay garantía de salida a internet (y api.ejemplo.com no existe),
el "servidor remoto" es local: un http.server que tarda DEMORA segundos
en contestar /cosas. Se puede apuntar a otro con DATOS_URL=...

Uso:
    pip install fastapi uvicorn httpx requests
    python3 ej5_datos.py               # API en 8002, remoto falso en 8003
    PUERTO=30020 PUERTO_REMOTO=30021 python3 ej5_datos.py
"""
import asyncio
import http.server
import json
import multiprocessing
import os
import threading
import time

import httpx
import requests
from fastapi import FastAPI

PUERTO = int(os.environ.get('PUERTO', 8002))
PUERTO_REMOTO = int(os.environ.get('PUERTO_REMOTO', 8003))
URL = os.environ.get('DATOS_URL', f'http://127.0.0.1:{PUERTO_REMOTO}/cosas')
PEDIDOS = 3
DEMORA = 1.0

app = FastAPI()


@app.get('/datos-mal')
async def datos_mal():
    """El de la consigna: requests es sincrónico y bloquea el loop entero."""
    return requests.get(URL, timeout=10).json()


@app.get('/datos-def')
def datos_def():
    """Arreglo 1: def común. FastAPI lo corre en el threadpool."""
    return requests.get(URL, timeout=10).json()


@app.get('/datos-httpx')
async def datos_httpx():
    """Arreglo 2: biblioteca async. El await cede el control mientras espera."""
    async with httpx.AsyncClient(timeout=10) as cliente:
        r = await cliente.get(URL)
        return r.json()


# ---------------------------------------------------------------
# El "servidor remoto" lento, con la stdlib (clase 19, primera mitad)
# ---------------------------------------------------------------

class Remoto(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        time.sleep(DEMORA)                    # simula una API lenta
        cuerpo = json.dumps({'cosas': [1, 2, 3]}).encode()
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(cuerpo)))
        self.end_headers()
        self.wfile.write(cuerpo)

    def log_message(self, *args):
        pass


def levantar_api():
    import uvicorn
    uvicorn.run(app, host='127.0.0.1', port=PUERTO, log_level='error')


async def medir(ruta):
    async with httpx.AsyncClient(timeout=30) as cliente:
        t0 = time.perf_counter()
        respuestas = await asyncio.gather(*(
            cliente.get(f'http://127.0.0.1:{PUERTO}/{ruta}') for _ in range(PEDIDOS)))
        for r in respuestas:
            r.raise_for_status()
        return time.perf_counter() - t0


async def correr():
    print(f'{PEDIDOS} pedidos concurrentes; el remoto tarda {DEMORA}s cada uno:\n')
    for ruta in ('datos-mal', 'datos-def', 'datos-httpx'):
        print(f'  /{ruta:<12} {await medir(ruta):5.2f}s')


def main():
    remoto = http.server.ThreadingHTTPServer(('127.0.0.1', PUERTO_REMOTO), Remoto)
    threading.Thread(target=remoto.serve_forever, daemon=True).start()
    api = multiprocessing.Process(target=levantar_api, daemon=True)
    api.start()
    time.sleep(3)
    try:
        asyncio.run(correr())
    finally:
        api.terminate()
        api.join(timeout=5)
        remoto.shutdown()


if __name__ == '__main__':
    main()
