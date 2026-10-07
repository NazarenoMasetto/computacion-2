#!/usr/bin/env python3
"""Ejercicio 2: productor-consumidor con una cola limitada hecha con Condition."""
import random
import threading
import time


class ColaLimitada:
    """Cola FIFO de tamaño máximo fijo, protegida por una Condition."""

    def __init__(self, maxsize):
        self.maxsize = maxsize
        self.items = []
        self.condition = threading.Condition()

    def put(self, item, timeout=None):
        """Agrega un item. Bloquea si está llena."""
        with self.condition:
            # while (no if): al despertar hay que volver a chequear la condición
            while len(self.items) >= self.maxsize:
                if not self.condition.wait(timeout):
                    raise TimeoutError("Timeout esperando espacio")
            self.items.append(item)
            self.condition.notify()

    def get(self, timeout=None):
        """Obtiene un item. Bloquea si está vacía."""
        with self.condition:
            while len(self.items) == 0:
                if not self.condition.wait(timeout):
                    raise TimeoutError("Timeout esperando item")
            item = self.items.pop(0)
            self.condition.notify()
            return item

    def size(self):
        with self.condition:
            return len(self.items)


cola = ColaLimitada(5)
terminado = threading.Event()
consumidos = []                 # para verificar al final que no se perdió nada
lock_consumidos = threading.Lock()


def productor(id, cantidad):
    for i in range(cantidad):
        item = f"P{id}-{i}"
        cola.put(item)
        print(f"[Prod-{id}] Produjo {item}, cola={cola.size()}")
        time.sleep(random.uniform(0.1, 0.3))
    print(f"[Prod-{id}] Terminó")


def consumidor(id):
    while not (terminado.is_set() and cola.size() == 0):
        try:
            item = cola.get(timeout=0.5)
            with lock_consumidos:
                consumidos.append(item)
            print(f"[Cons-{id}] Consumió {item}, cola={cola.size()}")
            time.sleep(random.uniform(0.2, 0.4))
        except TimeoutError:
            pass
    print(f"[Cons-{id}] Terminó")


if __name__ == "__main__":
    threads = []
    for i in range(2):
        threads.append(threading.Thread(target=productor, args=(i, 5)))
    for i in range(3):
        threads.append(threading.Thread(target=consumidor, args=(i,)))

    for t in threads:
        t.start()

    # Esperar productores
    for t in threads[:2]:
        t.join()

    terminado.set()

    for t in threads[2:]:
        t.join()

    print(f"Items consumidos: {len(consumidos)} (esperados 10)")
    print("Fin del programa")
