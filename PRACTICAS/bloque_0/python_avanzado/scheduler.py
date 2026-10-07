#!/usr/bin/env python3
"""Ejercicio 4.2 - Scheduler de coroutines basado en generadores.

Cada tarea es un generador; cada `yield` cede el control. El scheduler las
ejecuta en round-robin: avanza una un paso, la vuelve a encolar al final, y
cuando una termina (StopIteration) la saca de la cola. Es la idea base del
event loop de asyncio (sin I/O ni esperas).
"""

from collections import deque
from typing import Generator


class Scheduler:
    """Planificador round-robin de generadores."""

    def __init__(self) -> None:
        self.cola: deque[Generator] = deque()

    def add(self, tarea: Generator) -> None:
        if not hasattr(tarea, "__next__"):
            raise TypeError("la tarea debe ser un generador (llamá a la función: tarea())")
        self.cola.append(tarea)

    def run(self) -> None:
        while self.cola:
            tarea = self.cola.popleft()
            try:
                next(tarea)             # ejecuta hasta el próximo yield
            except StopIteration:
                continue                # terminó: no se vuelve a encolar
            except Exception as e:      # una tarea rota no tumba a las demás
                print(f"[Scheduler] tarea {getattr(tarea, '__name__', tarea)} falló: {e!r}")
                continue
            self.cola.append(tarea)


def tarea_a():
    for i in range(3):
        print(f"Tarea A: paso {i}")
        yield


def tarea_b():
    for i in range(5):
        print(f"Tarea B: paso {i}")
        yield


if __name__ == "__main__":
    scheduler = Scheduler()
    scheduler.add(tarea_a())
    scheduler.add(tarea_b())
    scheduler.run()

    print("--- Una tarea que falla no frena a las otras ---")

    def rota():
        yield
        raise ValueError("ups")

    s2 = Scheduler()
    s2.add(rota())
    s2.add(tarea_a())
    s2.run()
