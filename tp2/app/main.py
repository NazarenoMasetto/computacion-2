"""API HTTP de la plataforma de tareas."""
import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException

from .modelos import Estado, Tarea, TareaIn
from .pool import Pool

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s %(levelname)s [%(name)s] %(message)s")

N_WORKERS = int(os.getenv("WORKERS", "4"))
TIMEOUT_DEFAULT = float(os.getenv("TIMEOUT_DEFAULT", "30"))
ESPERA_APAGADO = float(os.getenv("ESPERA_APAGADO", "10"))
DIR_ESTADO = Path(os.getenv("DIR_ESTADO", "datos"))

log = logging.getLogger("api")
pool = Pool(N_WORKERS, TIMEOUT_DEFAULT)


def _reportar_volcado_previo() -> None:
    volcados = sorted(DIR_ESTADO.glob("estado_*.json"))
    if volcados:
        log.info("Encontré %d volcado(s) previo(s); el último es %s",
                 len(volcados), volcados[-1])
    else:
        log.info("No hay volcados previos en %s", DIR_ESTADO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- arranque ---
    _reportar_volcado_previo()
    pool.iniciar()      # arranca los workers dentro del event loop de uvicorn
    yield
    # --- apagado ---
    # Uvicorn ya instaló handlers para SIGTERM y SIGINT: al recibir una de
    # esas señales deja de aceptar conexiones, termina las requests abiertas
    # y recién ahí ejecuta este bloque.
    await pool.apagar(ESPERA_APAGADO, DIR_ESTADO)


app = FastAPI(title="Plataforma de Tareas Distribuidas", lifespan=lifespan)


def _buscar(tarea_id: str) -> Tarea:
    tarea = pool.tareas.get(tarea_id)
    if tarea is None:
        raise HTTPException(404, f"No existe la tarea {tarea_id}")
    return tarea


@app.post("/tareas", status_code=202)
async def crear_tarea(datos: TareaIn) -> Tarea:
    # 202 Accepted: "la recibí, todavía no la hice".
    try:
        return pool.encolar(datos)
    except RuntimeError as e:
        raise HTTPException(503, str(e))


@app.get("/tareas")
async def listar_tareas(estado: Estado | None = None) -> list[Tarea]:
    return [t for t in pool.tareas.values() if estado is None or t.estado == estado]


@app.get("/tareas/{tarea_id}")
async def ver_tarea(tarea_id: str) -> Tarea:
    return _buscar(tarea_id)


@app.delete("/tareas/{tarea_id}")
async def cancelar_tarea(tarea_id: str) -> Tarea:
    tarea = _buscar(tarea_id)
    if not pool.cancelar(tarea_id):
        raise HTTPException(409, f"La tarea ya terminó ({tarea.estado.value})")
    return tarea


@app.get("/estadisticas")
async def estadisticas() -> dict:
    return pool.estadisticas()
