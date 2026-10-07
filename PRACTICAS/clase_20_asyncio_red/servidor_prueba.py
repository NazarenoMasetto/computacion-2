#!/usr/bin/env python3
"""Servidor HTTP local para probar las descargas del ejercicio 3.

Reemplaza a https://example.com cuando no hay salida a internet (o para
tener demoras controladas). Responde una página de ~1 KB después de
esperar `demora` segundos (por defecto 0.5).

Uso:
    python3 servidor_prueba.py [puerto]     # por defecto 8085 (o PUERTO=...)
    curl 'localhost:8085/?demora=1'
"""
import asyncio
import os
import sys

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI()
PAGINA = '<html><body>' + 'contenido de prueba ' * 50 + '</body></html>'


@app.get('/', response_class=HTMLResponse)
async def pagina(demora: float = 0.5):
    await asyncio.sleep(demora)          # simula la latencia de un sitio real
    return PAGINA


if __name__ == '__main__':
    import uvicorn
    puerto = int(sys.argv[1]) if len(sys.argv) > 1 else int(os.environ.get('PUERTO', 8085))
    uvicorn.run(app, host='127.0.0.1', port=puerto, log_level='warning',
                backlog=2048)
