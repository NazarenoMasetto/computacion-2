#!/usr/bin/env python3
"""Ejercicio adicional: monitor de locks y semáforos en tiempo real.

Envolvemos Lock y Semaphore en clases "monitoreadas" que registran quién
tiene el recurso y quién está esperando. Un thread monitor imprime ese
estado cada cierto intervalo mientras los workers trabajan.

Uso:
    python3 ej_adicional_monitor.py [segundos]   # default 3
"""
import random
import sys
import threading
import time


class LockMonitoreado:
    """Lock que sabe quién lo tiene y quién está esperando."""

    def __init__(self, nombre):
        self.nombre = nombre
        self._lock = threading.Lock()
        self._info = threading.Lock()   # protege los datos de monitoreo
        self.duenio = None
        self.esperando = []
        self.adquisiciones = 0

    def acquire(self):
        yo = threading.current_thread().name
        with self._info:
            self.esperando.append(yo)
        self._lock.acquire()
        with self._info:
            self.esperando.remove(yo)
            self.duenio = yo
            self.adquisiciones += 1

    def release(self):
        with self._info:
            self.duenio = None
        self._lock.release()

    __enter__ = acquire

    def __exit__(self, *args):
        self.release()

    def estado(self):
        with self._info:
            return (f"Lock {self.nombre}: dueño={self.duenio or '-'} "
                    f"esperando={self.esperando} total={self.adquisiciones}")


class SemaforoMonitoreado:
    """Semáforo que lleva la lista de threads adentro y afuera esperando."""

    def __init__(self, nombre, valor):
        self.nombre = nombre
        self.capacidad = valor
        self._sem = threading.Semaphore(valor)
        self._info = threading.Lock()
        self.adentro = []
        self.esperando = []

    def acquire(self):
        yo = threading.current_thread().name
        with self._info:
            self.esperando.append(yo)
        self._sem.acquire()
        with self._info:
            self.esperando.remove(yo)
            self.adentro.append(yo)

    def release(self):
        with self._info:
            self.adentro.remove(threading.current_thread().name)
        self._sem.release()

    __enter__ = acquire

    def __exit__(self, *args):
        self.release()

    def estado(self):
        with self._info:
            libres = self.capacidad - len(self.adentro)
            return (f"Sem  {self.nombre}: libres={libres}/{self.capacidad} "
                    f"adentro={self.adentro} esperando={self.esperando}")


def monitor(recursos, parar, intervalo=0.5):
    """Imprime el estado de todos los recursos periódicamente."""
    while not parar.wait(intervalo):
        print(f"--- t={time.strftime('%H:%M:%S')} ---")
        for r in recursos:
            print("   " + r.estado())


def worker(lock, sem, parar):
    while not parar.is_set():
        with sem:                       # como mucho N a la vez en la "BD"
            time.sleep(random.uniform(0.1, 0.4))
            with lock:                  # sección crítica corta: escribir log
                time.sleep(random.uniform(0.05, 0.15))
        time.sleep(random.uniform(0.0, 0.2))


if __name__ == "__main__":
    duracion = float(sys.argv[1]) if len(sys.argv) > 1 else 3
    lock = LockMonitoreado("log")
    sem = SemaforoMonitoreado("bd", 2)
    parar = threading.Event()

    workers = [threading.Thread(target=worker, args=(lock, sem, parar), name=f"W{i}")
               for i in range(5)]
    mon = threading.Thread(target=monitor, args=([lock, sem], parar), name="monitor")
    for t in workers + [mon]:
        t.start()

    time.sleep(duracion)
    parar.set()
    for t in workers + [mon]:
        t.join()
    print("Estado final:")
    print("   " + lock.estado())
    print("   " + sem.estado())
