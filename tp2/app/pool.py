"""Cola de tareas + pool de workers (productor-consumidor con corrutinas)."""
import asyncio
import json
import logging
import time
import uuid
from pathlib import Path

from .modelos import FINALES, Estado, Tarea, TareaIn
from .tareas import ejecutar

log = logging.getLogger("pool")


class Pool:
    def __init__(self, n_workers: int, timeout_default: float):
        self.n_workers = n_workers
        self.timeout_default = timeout_default
        self.tareas: dict[str, Tarea] = {}          # el "almacén" en memoria
        self.cola: asyncio.Queue[str] = asyncio.Queue()
        self.en_curso: dict[str, asyncio.Task] = {}  # id -> Task en ejecución
        self._workers: list[asyncio.Task] = []
        self.aceptando = True

    # ---------- ciclo de vida ----------

    def iniciar(self) -> None:
        self._workers = [asyncio.create_task(self._worker(i), name=f"worker-{i}")
                         for i in range(self.n_workers)]
        log.info("Pool iniciado con %d workers", self.n_workers)

    async def apagar(self, espera_max: float, directorio: Path) -> Path:
        """Apagado ordenado. Lo llama el lifespan cuando uvicorn recibe
        SIGTERM/SIGINT."""
        # 1) Dejar de aceptar tareas nuevas (el POST pasa a responder 503).
        self.aceptando = False
        log.info("Apagando: %d tareas en curso, %d en cola",
                 len(self.en_curso), self.cola.qsize())

        # 2) Esperar a las que están ejecutando, con límite.
        if self.en_curso:
            _, pendientes = await asyncio.wait(
                list(self.en_curso.values()), timeout=espera_max)
            if pendientes:
                log.warning("%d tareas no terminaron en %ss, se cancelan",
                            len(pendientes), espera_max)
                for tarea_id, job in list(self.en_curso.items()):
                    self._finalizar(self.tareas[tarea_id], Estado.CANCELADA,
                                    error="cancelada por apagado del servidor")
                    job.cancel()
                # Esperar a que procesen la cancelación (corran sus finally,
                # cierren conexiones, etc.) antes de seguir.
                await asyncio.wait(pendientes)

        # 3) Cancelar los workers y esperar a que terminen de verdad
        #    (así no queda ninguna corrutina huérfana).
        for w in self._workers:
            w.cancel()
        await asyncio.gather(*self._workers, return_exceptions=True)

        # 4) Volcar el estado a JSON.
        return self.volcar(directorio)

    def volcar(self, directorio: Path) -> Path:
        directorio.mkdir(parents=True, exist_ok=True)
        marca = time.strftime("%Y%m%d_%H%M%S")
        archivo = directorio / f"estado_{marca}.json"
        datos = {
            "volcado": marca,
            "estadisticas": self.estadisticas(),
            "tareas": [t.model_dump(mode="json") for t in self.tareas.values()],
        }
        # Escritura síncrona: está bien acá porque es una sola vez, al final,
        # cuando ya no hay requests que atender.
        archivo.write_text(json.dumps(datos, indent=2, ensure_ascii=False))
        log.info("Estado volcado en %s (%d tareas)", archivo, len(self.tareas))
        return archivo

    # ---------- operaciones que usa la API ----------

    def encolar(self, datos: TareaIn) -> Tarea:
        if not self.aceptando:
            raise RuntimeError("el servidor se está apagando")
        tarea = Tarea(
            id=uuid.uuid4().hex[:8],
            tipo=datos.tipo,
            parametros=datos.parametros,
            timeout=datos.timeout or self.timeout_default,
            creada=time.time(),
        )
        self.tareas[tarea.id] = tarea
        # put_nowait: la cola no tiene límite, así que no hace falta await
        # y el POST vuelve en el acto, sin esperar a que la tarea corra.
        self.cola.put_nowait(tarea.id)
        return tarea

    def cancelar(self, tarea_id: str) -> bool:
        """Devuelve False si la tarea ya había terminado."""
        tarea = self.tareas[tarea_id]
        if tarea.estado in FINALES:
            return False
        # Marcamos primero: si está pendiente, el worker la va a saltear
        # al sacarla de la cola. Si está ejecutando, cancelamos su Task.
        self._finalizar(tarea, Estado.CANCELADA, error="cancelada por el usuario")
        job = self.en_curso.get(tarea_id)
        if job:
            job.cancel()
        return True

    # ---------- el worker ----------

    async def _worker(self, n: int) -> None:
        while True:
            tarea_id = await self.cola.get()   # se suspende hasta que haya algo
            try:
                await self._procesar(self.tareas[tarea_id])
            finally:
                self.cola.task_done()

    async def _procesar(self, tarea: Tarea) -> None:
        if tarea.estado == Estado.CANCELADA:   # la cancelaron estando en cola
            return
        if not self.aceptando:
            # Estamos apagando: no arrancamos nada nuevo. Queda "pendiente"
            # y así aparece en el volcado.
            return

        tarea.estado = Estado.EJECUTANDO
        tarea.iniciada = time.time()
        # La tarea corre en su propia Task para poder cancelarla sola,
        # sin matar al worker que la está esperando.
        job = asyncio.create_task(ejecutar(tarea))
        self.en_curso[tarea.id] = job
        try:
            resultado = await asyncio.wait_for(job, timeout=tarea.timeout)
            # Si un DELETE llegó justo cuando el job terminaba, la tarea ya
            # quedó "cancelada" y no hay que pisar ese estado.
            if tarea.estado == Estado.EJECUTANDO:
                tarea.resultado = resultado
                self._finalizar(tarea, Estado.COMPLETADA)
        except asyncio.TimeoutError:
            # wait_for ya canceló el job antes de lanzar esto.
            if tarea.estado == Estado.EJECUTANDO:
                self._finalizar(tarea, Estado.FALLIDA,
                                error=f"timeout: superó {tarea.timeout}s")
        except asyncio.CancelledError:
            # ¿Quién recibió la cancelación? cancelling() > 0 significa que
            # alguien pidió cancelar AL WORKER (apagado): hay que propagarla.
            # Si es 0, lo cancelado fue solo el job (un DELETE): el worker
            # se traga la excepción y sigue atendiendo la cola.
            if asyncio.current_task().cancelling():
                job.cancel()
                raise
        except Exception as e:  # cualquier error de la tarea
            log.exception("Tarea %s falló", tarea.id)
            if tarea.estado == Estado.EJECUTANDO:
                self._finalizar(tarea, Estado.FALLIDA,
                                error=f"{type(e).__name__}: {e}")
        finally:
            self.en_curso.pop(tarea.id, None)

    @staticmethod
    def _finalizar(tarea: Tarea, estado: Estado, error: str | None = None) -> None:
        tarea.estado = estado
        tarea.error = error
        tarea.finalizada = time.time()

    # ---------- estadísticas ----------

    def estadisticas(self) -> dict:
        por_estado = {e.value: 0 for e in Estado}
        duraciones = []
        for t in self.tareas.values():
            por_estado[t.estado.value] += 1
            if t.estado == Estado.COMPLETADA:
                duraciones.append(t.finalizada - t.iniciada)
        return {
            "total": len(self.tareas),
            "por_estado": por_estado,
            "tiempo_promedio_s": (round(sum(duraciones) / len(duraciones), 4)
                                  if duraciones else None),
            "workers": self.n_workers,
            # Si un worker muriera por un bug del pool, se vería acá.
            "workers_vivos": sum(1 for w in self._workers if not w.done()),
            "workers_ocupados": len(self.en_curso),
            "en_cola": self.cola.qsize(),
        }
