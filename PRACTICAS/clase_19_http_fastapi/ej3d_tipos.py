#!/usr/bin/env python3
"""Ejercicio 3, parte D: los tipos importan.

Mini API con las dos variantes que pide la consigna, al lado de la
versión correcta, para comparar sin tocar api.py:

    GET  /con-tipo/{tarea_id}   tarea_id: int   (como api.py)
    GET  /sin-tipo/{tarea_id}   sin anotación   (punto 11)
    POST /prioridad-int         prioridad: int  (como api.py)
    POST /prioridad-str         prioridad: str  (punto 12)

Uso:
    python3 ej3d_tipos.py [puerto]      # por defecto 8000
"""
import os
import sys

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(title='Tipos')

# Mismas claves enteras que usa api.py
tareas = {1: {'id': 1, 'tipo': 'esperar'}}


@app.get('/con-tipo/{tarea_id}')
async def con_tipo(tarea_id: int):
    if tarea_id not in tareas:
        raise HTTPException(status_code=404, detail='No existe esa tarea')
    return tareas[tarea_id]


@app.get('/sin-tipo/{tarea_id}')
async def sin_tipo(tarea_id):
    # Sin anotación FastAPI lo trata como str: nadie lo convierte ni valida.
    if tarea_id not in tareas:
        raise HTTPException(
            status_code=404,
            detail=f'No existe esa tarea (recibí {tarea_id!r}, de tipo {type(tarea_id).__name__})',
        )
    return tareas[tarea_id]


class ConInt(BaseModel):
    prioridad: int = Field(default=1, ge=1, le=5)


class ConStr(BaseModel):
    prioridad: str


@app.post('/prioridad-int')
async def prioridad_int(datos: ConInt):
    return {'prioridad': datos.prioridad, 'tipo': type(datos.prioridad).__name__}


@app.post('/prioridad-str')
async def prioridad_str(datos: ConStr):
    return {'prioridad': datos.prioridad, 'tipo': type(datos.prioridad).__name__}


if __name__ == '__main__':
    import uvicorn
    puerto = int(sys.argv[1]) if len(sys.argv) > 1 else int(os.environ.get('PUERTO', 8000))
    uvicorn.run(app, host='127.0.0.1', port=puerto)
