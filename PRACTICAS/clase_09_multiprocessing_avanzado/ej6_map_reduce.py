#!/usr/bin/env python3
"""
Ejercicio 6: Map-Reduce para conteo de palabras.

Uso:
  python3 ej6_map_reduce.py                 -> cuenta palabras de los TEXTOS de ejemplo
  python3 ej6_map_reduce.py archivo.txt [N] -> extensión: divide el archivo en chunks de N líneas
"""
from multiprocessing import Pool
from functools import reduce
import string
import sys

TEXTOS = [
    "el rapido zorro marron salta sobre el perro perezoso",
    "el perro duerme bajo el arbol mientras el zorro corre",
    "rapido como el viento el zorro vuelve a saltar sobre el perro",
    "el arbol es viejo y el perro lo mira con curiosidad",
    "saltar correr el zorro y el perro juegan bajo el arbol",
]

# Para limpiar signos de puntuación al procesar archivos reales
TABLA_PUNTUACION = str.maketrans("", "", string.punctuation + "¿¡«»")


def mapper(texto):
    """Cuenta palabras en un texto (etapa map)."""
    conteo = {}
    for palabra in texto.lower().translate(TABLA_PUNTUACION).split():
        conteo[palabra] = conteo.get(palabra, 0) + 1
    return conteo


def reducer(dict1, dict2):
    """Combina dos diccionarios de conteo (etapa reduce)."""
    resultado = dict1.copy()
    for palabra, count in dict2.items():
        resultado[palabra] = resultado.get(palabra, 0) + count
    return resultado


def leer_chunks(ruta, lineas_por_chunk):
    """Generador: divide el archivo en chunks de N líneas (cada chunk es un string)."""
    chunk = []
    with open(ruta, encoding="utf-8", errors="replace") as f:
        for linea in f:
            chunk.append(linea)
            if len(chunk) == lineas_por_chunk:
                yield "".join(chunk)
                chunk = []
    if chunk:
        yield "".join(chunk)


if __name__ == "__main__":
    with Pool(4) as pool:
        if len(sys.argv) > 1:
            # Extensión: archivo grande dividido en chunks
            ruta = sys.argv[1]
            n = int(sys.argv[2]) if len(sys.argv) > 2 else 1000
            conteos_parciales = list(pool.imap_unordered(mapper, leer_chunks(ruta, n)))
            print(f"Archivo {ruta}: {len(conteos_parciales)} chunks de hasta {n} líneas")
        else:
            # Map: contar en paralelo
            conteos_parciales = pool.map(mapper, TEXTOS)

    # Reduce: combinar resultados (secuencial)
    conteo_total = reduce(reducer, conteos_parciales, {})

    # Ordenar por frecuencia descendente (y alfabético para desempatar)
    palabras_ordenadas = sorted(conteo_total.items(), key=lambda x: (-x[1], x[0]))

    print("Top palabras más frecuentes:")
    for palabra, count in palabras_ordenadas[:10]:
        print(f"  {palabra:15s} {count}")
