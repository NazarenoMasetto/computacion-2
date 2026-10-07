#!/usr/bin/env python3
"""Ejercicio 3: productor-consumidor con multiprocessing.Queue."""
import multiprocessing
import os
import random
import time

FIN = None  # "píldora venenosa": avisa al consumidor que no vienen más items


def productor(cola, cantidad=10):
    """Genera `cantidad` items y los pone en la cola."""
    for i in range(1, cantidad + 1):
        item = {"id": i, "valor": random.randint(1, 100)}
        cola.put(item)
        print(f"[Productor {os.getpid()}] produje {item}", flush=True)
        time.sleep(random.uniform(0.05, 0.2))
    cola.put(FIN)
    print("[Productor] terminé", flush=True)


def consumidor(cola, resultados):
    """Saca items hasta recibir FIN; procesa cada uno (valor al cuadrado)."""
    procesados = 0
    while True:
        item = cola.get()  # bloquea hasta que haya algo
        if item is FIN:
            break
        resultado = item["valor"] ** 2
        print(f"    [Consumidor {os.getpid()}] item {item['id']}: {item['valor']}² = {resultado}", flush=True)
        procesados += 1
        time.sleep(random.uniform(0.05, 0.3))
    resultados.put(procesados)
    print("    [Consumidor] terminé", flush=True)


def main():
    cola = multiprocessing.Queue()
    resultados = multiprocessing.Queue()

    prod = multiprocessing.Process(target=productor, args=(cola,))
    cons = multiprocessing.Process(target=consumidor, args=(cola, resultados))
    prod.start()
    cons.start()
    prod.join()
    cons.join()

    print(f"\nItems procesados por el consumidor: {resultados.get()}")


if __name__ == "__main__":
    main()
