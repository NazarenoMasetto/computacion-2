#!/usr/bin/env python3
"""Una API con FastAPI: validación, errores y documentación automática.

Versión resuelta del ejercicio 3 (obligatorio) de la clase 19. Sobre el
api.py de la cátedra se agregó:

    - PATCH /tareas/{id}   cambia solo el estado (modelo con campos opcionales)
    - GET /estadisticas    cantidad de tareas por estado
    - POST /tareas         rechaza con 409 si ya hay 10 pendientes
    - un print en crear() para ver que la validación ocurre ANTES
    - middleware que agrega el header X-Tiempo (ejercicio adicional)

Uso:
    python3 api.py                 # puerto 8000
    python3 api.py 30000           # otro puerto (o PUERTO=30000)
    uvicorn api:app --port 30000 --workers 3

Después:
    http://localhost:8000/docs        <- la documentación se genera sola
    curl localhost:8000/tareas
    curl -X POST localhost:8000/tareas -H 'Content-Type: application/json' \
         -d '{"tipo":"descargar","prioridad":3}'
"""
import asyncio
import os
import sys
import threading
import time
from collections import Counter
from typing import Literal

from fastapi import FastAPI, HTTPException, Query, Request
from pydantic import BaseModel, Field

app = FastAPI(
    title='Tareas',
    description='Ejemplo de la clase 19: HTTP + FastAPI',
)

# Estado en memoria. OJO: con --workers > 1 cada proceso tiene el suyo.
tareas: dict[int, dict] = {}
proximo_id = 0

MAX_PENDIENTES = 10
Estado = Literal['pendiente', 'ejecutando', 'completada']


# ---------------------------------------------------------------
# Modelos: Pydantic valida por nosotros
# ---------------------------------------------------------------

class TareaNueva(BaseModel):
    """Lo que el cliente manda en el cuerpo de un POST."""
    tipo: Literal['descargar', 'hashear', 'esperar']
    prioridad: int = Field(default=1, ge=1, le=5,
                           description='1 = más baja, 5 = más alta')


class Tarea(TareaNueva):
    """Lo que devolvemos: lo anterior más lo que agrega el servidor."""
    id: int
    estado: Estado = 'pendiente'


class TareaParcial(BaseModel):
    """Cuerpo del PATCH: todos los campos son opcionales.

    La consigna pide cambiar solo el estado, así que es el único campo.
    Si no viene, el PATCH no cambia nada.
    """
    estado: Estado | None = None


# ---------------------------------------------------------------
# Middleware (adicional): mide cuánto tarda cada pedido
# ---------------------------------------------------------------

@app.middleware('http')
async def medir_tiempo(request: Request, call_next):
    """Envuelve al endpoint: lo de antes de call_next corre antes, lo de
    después corre cuando el endpoint ya devolvió la respuesta."""
    t0 = time.perf_counter()
    respuesta = await call_next(request)        # acá adentro corre el endpoint
    respuesta.headers['X-Tiempo'] = f'{(time.perf_counter() - t0) * 1000:.2f}ms'
    return respuesta


# ---------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------

@app.get('/')
async def raiz():
    """FastAPI convierte el dict a JSON y pone los headers por su cuenta."""
    return {'servicio': 'tareas', 'docs': '/docs'}


@app.get('/tareas', response_model=list[Tarea])
async def listar(
    estado: str | None = Query(default=None, description='Filtrar por estado'),
    limite: int = Query(default=10, ge=1, le=100),
):
    """Los parámetros que no están en la ruta se leen de la query string.
    Los tipos NO son decorativos: FastAPI valida y convierte."""
    items = list(tareas.values())
    if estado:
        items = [t for t in items if t['estado'] == estado]
    return items[:limite]


@app.post('/tareas', response_model=Tarea, status_code=201)
async def crear(nueva: TareaNueva):
    """201 Created es la respuesta correcta a un POST que crea algo."""
    # Si este print sale, el cuerpo YA fue validado: con datos inválidos
    # FastAPI responde 422 sin llegar a ejecutar esta función.
    print(f'[crear] ejecutando con {nueva!r}', flush=True)

    pendientes = sum(1 for t in tareas.values() if t['estado'] == 'pendiente')
    if pendientes >= MAX_PENDIENTES:
        # 409 Conflict: el pedido es válido, pero choca con el estado
        # actual del recurso (la cola ya está llena).
        raise HTTPException(
            status_code=409,
            detail=f'Ya hay {pendientes} tareas pendientes (máximo {MAX_PENDIENTES})',
        )

    global proximo_id
    proximo_id += 1
    tarea = {'id': proximo_id, **nueva.model_dump(), 'estado': 'pendiente'}
    tareas[proximo_id] = tarea
    return tarea


@app.get('/tareas/{tarea_id}', response_model=Tarea)
async def obtener(tarea_id: int):
    """El : int hace que /tareas/abc devuelva 422 sin ejecutar la función."""
    if tarea_id not in tareas:
        raise HTTPException(status_code=404, detail='No existe esa tarea')
    return tareas[tarea_id]


@app.patch('/tareas/{tarea_id}', response_model=Tarea)
async def modificar(tarea_id: int, cambios: TareaParcial):
    """Modifica solo los campos que vinieron en el cuerpo."""
    if tarea_id not in tareas:
        raise HTTPException(status_code=404, detail='No existe esa tarea')
    # exclude_unset: solo lo que el cliente mandó de verdad
    tareas[tarea_id].update(cambios.model_dump(exclude_unset=True))
    return tareas[tarea_id]


@app.delete('/tareas/{tarea_id}', status_code=204)
async def borrar(tarea_id: int):
    """204 No Content: salió bien y no hay nada que devolver."""
    if tarea_id not in tareas:
        raise HTTPException(status_code=404, detail='No existe esa tarea')
    del tareas[tarea_id]


@app.get('/estadisticas')
async def estadisticas():
    """Cantidad de tareas por estado (incluye los estados en cero)."""
    conteo = Counter(t['estado'] for t in tareas.values())
    por_estado = {e: conteo.get(e, 0)
                  for e in ('pendiente', 'ejecutando', 'completada')}
    return {'total': len(tareas), 'por_estado': por_estado}


@app.get('/quien-soy')
async def quien_soy():
    """Dónde corre realmente un endpoint async."""
    loop = asyncio.get_running_loop()
    return {
        'pid': os.getpid(),
        'thread': threading.current_thread().name,
        'loop': type(loop).__name__,
        'id_del_loop': id(loop),        # igual en todos los pedidos
    }


@app.get('/quien-soy-sync')
def quien_soy_sync():
    """Un def común NO corre en el event loop: va a un threadpool."""
    try:
        asyncio.get_running_loop()
        estado = 'HAY loop'
    except RuntimeError:
        estado = 'NO hay loop corriendo acá'
    return {'thread': threading.current_thread().name, 'loop': estado}


if __name__ == '__main__':
    import uvicorn
    puerto = int(sys.argv[1]) if len(sys.argv) > 1 else int(os.environ.get('PUERTO', 8000))
    # uvicorn es el que crea y corre el event loop; FastAPI solo responde.
    uvicorn.run(app, host='127.0.0.1', port=puerto)
