#!/usr/bin/env python3
"""
Ejercicio 5 (obligatorio): procesador de imágenes paralelo.
Simula imágenes como matrices de enteros y les aplica un blur 3x3,
comparando procesamiento secuencial contra Pool.map.

Uso: python3 ej5_procesador_imagenes.py [num_imagenes] [size] [workers]
"""
from multiprocessing import Pool
import random
import sys
import time


def crear_imagen(size):
    """Crea una 'imagen' como lista de listas."""
    return [[random.randint(0, 255) for _ in range(size)] for _ in range(size)]


def aplicar_filtro(imagen):
    """Aplica un filtro blur 3x3 (CPU-intensive)."""
    size = len(imagen)
    resultado = [[0] * size for _ in range(size)]

    for i in range(1, size - 1):
        for j in range(1, size - 1):
            suma = 0
            for di in (-1, 0, 1):
                for dj in (-1, 0, 1):
                    suma += imagen[i + di][j + dj]
            resultado[i][j] = suma // 9

    return resultado


def procesar_imagen(args):
    """Procesa una imagen y devuelve (idx, duración, checksum)."""
    idx, imagen = args
    inicio = time.time()
    resultado = aplicar_filtro(imagen)
    duracion = time.time() - inicio
    return idx, duracion, sum(sum(row) for row in resultado)


if __name__ == "__main__":
    NUM_IMAGENES = int(sys.argv[1]) if len(sys.argv) > 1 else 8
    SIZE = int(sys.argv[2]) if len(sys.argv) > 2 else 200
    WORKERS = int(sys.argv[3]) if len(sys.argv) > 3 else 4

    print(f"Creando {NUM_IMAGENES} imágenes de {SIZE}x{SIZE}...")
    imagenes = [(i, crear_imagen(SIZE)) for i in range(NUM_IMAGENES)]

    # Procesar secuencialmente
    print("\nProcesamiento secuencial:")
    inicio = time.time()
    checksums_seq = [procesar_imagen(img)[2] for img in imagenes]
    tiempo_secuencial = time.time() - inicio
    print(f"Tiempo: {tiempo_secuencial:.2f}s")

    # Procesar en paralelo
    print(f"\nProcesamiento paralelo ({WORKERS} workers):")
    inicio = time.time()
    with Pool(WORKERS) as pool:
        resultados = pool.map(procesar_imagen, imagenes)
    tiempo_paralelo = time.time() - inicio

    for idx, duracion, checksum in resultados:
        print(f"  Imagen {idx}: {duracion:.3f}s  checksum={checksum}")

    # Verificamos que el paralelo da lo mismo que el secuencial
    assert [r[2] for r in resultados] == checksums_seq, "¡Los resultados no coinciden!"

    print(f"Tiempo total: {tiempo_paralelo:.2f}s")
    print(f"Speedup: {tiempo_secuencial / tiempo_paralelo:.2f}x")
