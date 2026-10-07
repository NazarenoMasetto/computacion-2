#!/usr/bin/env python3
"""
Ejercicio 7 (preguntas): pipeline con una etapa lenta y cómo escalarla.
La etapa 2 tarda 4 veces más que las otras; se compara 1 worker vs 4 workers en esa etapa.
"""
from multiprocessing import Process, Queue
import time

N_ITEMS = 12
T_RAPIDA = 0.05
T_LENTA = 0.2


def etapa_multiplicar(input_q, output_q, n_siguientes):
    while True:
        item = input_q.get()
        if item is None:
            # Un None por cada worker de la etapa siguiente
            for _ in range(n_siguientes):
                output_q.put(None)
            break
        time.sleep(T_RAPIDA)
        output_q.put(item * 2)


def etapa_sumar_lenta(input_q, output_q):
    """Etapa cuello de botella. Puede haber varias copias leyendo la misma cola."""
    while True:
        item = input_q.get()
        if item is None:
            output_q.put(None)
            break
        time.sleep(T_LENTA)
        output_q.put(item + 10)


def etapa_formatear(input_q, output_q, n_anteriores):
    fines = 0
    while fines < n_anteriores:  # esperamos un None por cada worker anterior
        item = input_q.get()
        if item is None:
            fines += 1
            continue
        time.sleep(T_RAPIDA)
        output_q.put(f"resultado_{item:03d}")
    output_q.put(None)


def correr(n_lentos):
    q1, q2, q3, q4 = Queue(), Queue(), Queue(), Queue()
    procs = [Process(target=etapa_multiplicar, args=(q1, q2, n_lentos))]
    procs += [Process(target=etapa_sumar_lenta, args=(q2, q3)) for _ in range(n_lentos)]
    procs.append(Process(target=etapa_formatear, args=(q3, q4, n_lentos)))

    inicio = time.time()
    for p in procs:
        p.start()
    for i in range(N_ITEMS):
        q1.put(i)
    q1.put(None)

    resultados = []
    while (r := q4.get()) is not None:
        resultados.append(r)
    for p in procs:
        p.join()
    return time.time() - inicio, resultados


if __name__ == "__main__":
    for n in (1, 4):
        t, res = correr(n)
        print(f"Etapa lenta con {n} worker(s): {t:.2f}s  ({len(res)} resultados)")
        print(f"   orden de salida: {res[:6]} ...")
