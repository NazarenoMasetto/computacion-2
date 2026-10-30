"""Implementación de cada tipo de tarea."""
import asyncio
import hashlib
import threading
import time
from typing import Any

import httpx

from .modelos import Tarea, TipoTarea


# ---------------------------------------------------------------- esperar

async def esperar(segundos: float = 1) -> dict:
    # asyncio.sleep cede el control al event loop: mientras esta tarea
    # "duerme", el loop atiende requests y otros workers.
    # time.sleep() en cambio congelaría TODO el proceso esos segundos.
    await asyncio.sleep(segundos)
    return {"durmio": segundos}


# ---------------------------------------------------------------- descargar

async def _bajar_una(cliente: httpx.AsyncClient, url: str) -> dict:
    inicio = time.perf_counter()
    try:
        resp = await cliente.get(url)
        return {
            "url": url,
            "status": resp.status_code,
            "bytes": len(resp.content),
            "segundos": round(time.perf_counter() - inicio, 3),
        }
    except httpx.HTTPError as e:
        # Una URL rota no tira abajo toda la tarea: se reporta en su fila.
        return {
            "url": url,
            "error": f"{type(e).__name__}: {e}",
            "segundos": round(time.perf_counter() - inicio, 3),
        }


async def descargar(urls: list[str], concurrente: bool = True) -> dict:
    """Descarga las URLs. `concurrente=False` existe solo para la medición 1."""
    if not urls:
        raise ValueError("'urls' no puede estar vacía")
    inicio = time.perf_counter()
    # `async with` garantiza que las conexiones se cierren aunque la tarea
    # se cancele a mitad de una descarga (el CancelledError atraviesa el
    # bloque y __aexit__ libera el pool de conexiones).
    async with httpx.AsyncClient(timeout=10, follow_redirects=True) as cliente:
        if concurrente:
            # gather lanza todas las corrutinas a la vez: mientras una espera
            # la red, el loop avanza las otras. Tarda ~ lo que la más lenta.
            filas = await asyncio.gather(*(_bajar_una(cliente, u) for u in urls))
        else:
            # for + await: cada una empieza cuando terminó la anterior.
            # Tarda ~ la suma de todas.
            filas = [await _bajar_una(cliente, u) for u in urls]
    return {
        "modo": "concurrente" if concurrente else "secuencial",
        "total_segundos": round(time.perf_counter() - inicio, 3),
        "resultados": filas,
    }


# ---------------------------------------------------------------- hashear

_CHEQUEO_CADA = 10_000  # cada cuántas iteraciones mirar si nos cancelaron


def _hash_iterado(texto: str, iteraciones: int,
                  cancelar: threading.Event | None = None) -> str:
    """Función síncrona y CPU-bound. Corre en un thread del executor."""
    dato = texto.encode()
    for i in range(iteraciones):
        if cancelar is not None and i % _CHEQUEO_CADA == 0 and cancelar.is_set():
            raise RuntimeError("hash interrumpido")
        dato = hashlib.sha256(dato).digest()
    return dato.hex()


async def hashear(texto: str, iteraciones: int = 1_000_000,
                  bloqueante: bool = False) -> dict:
    """`bloqueante=True` corre el hash EN el event loop (mal a propósito):
    existe solo para la medición 2."""
    if iteraciones < 1:
        raise ValueError("'iteraciones' debe ser >= 1")
    inicio = time.perf_counter()

    if bloqueante:
        resultado = _hash_iterado(texto, iteraciones)   # congela el loop
    else:
        # to_thread manda la función a un thread del ThreadPoolExecutor por
        # defecto. El loop queda libre y se despierta cuando el thread termina.
        # Un thread no se puede matar desde afuera, así que la cancelación es
        # cooperativa: si nos cancelan, levantamos el Event y el thread corta
        # en el próximo chequeo en vez de seguir quemando CPU sin dueño.
        cancelar = threading.Event()
        try:
            resultado = await asyncio.to_thread(
                _hash_iterado, texto, iteraciones, cancelar)
        except asyncio.CancelledError:
            cancelar.set()
            raise

    return {
        "hash": resultado,
        "iteraciones": iteraciones,
        "en_executor": not bloqueante,
        "segundos": round(time.perf_counter() - inicio, 3),
    }


# ---------------------------------------------------------------- despacho

_DESPACHO = {
    TipoTarea.ESPERAR: esperar,
    TipoTarea.DESCARGAR: descargar,
    TipoTarea.HASHEAR: hashear,
}


async def ejecutar(tarea: Tarea) -> Any:
    """Despacha la tarea a la función que corresponde según su tipo."""
    funcion = _DESPACHO[tarea.tipo]
    return await funcion(**tarea.parametros)
