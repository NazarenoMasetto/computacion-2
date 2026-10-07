#!/usr/bin/env python3
"""Ejercicio 7: productor-consumidor con queue.Queue y un pool de 4 workers que procesan 20 imágenes."""
import queue
import threading
import time

NUM_WORKERS = 4
NUM_IMAGENES = 20

resultados = {}
resultados_lock = threading.Lock()


def procesar_imagen(nombre):
    """Simula procesar una imagen (0.5s)."""
    time.sleep(0.5)
    return f"{nombre} -> procesada"


def worker(q, worker_id):
    contador = 0
    while True:
        imagen = q.get()
        if imagen is None:  # señal de fin
            q.task_done()
            break
        resultado = procesar_imagen(imagen)
        print(f"Worker-{worker_id}: {resultado}")
        contador += 1
        q.task_done()

    with resultados_lock:
        resultados[f"Worker-{worker_id}"] = contador


if __name__ == "__main__":
    cola = queue.Queue()
    workers = [threading.Thread(target=worker, args=(cola, i)) for i in range(NUM_WORKERS)]
    for w in workers:
        w.start()

    inicio = time.perf_counter()
    # Productor: el hilo principal encola las imágenes
    for i in range(1, NUM_IMAGENES + 1):
        cola.put(f"imagen_{i:03d}.jpg")

    cola.join()  # espera a que se procesen todas

    for _ in workers:
        cola.put(None)
    for w in workers:
        w.join()

    tiempo = time.perf_counter() - inicio
    print(f"\nTiempo total: {tiempo:.2f}s (secuencial serían {NUM_IMAGENES * 0.5:.1f}s)")
    print("\nImágenes por worker:")
    for nombre, cant in sorted(resultados.items()):
        print(f"  {nombre}: {cant} imágenes")
    print(f"  Total: {sum(resultados.values())}")
