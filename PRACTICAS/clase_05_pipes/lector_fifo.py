#!/usr/bin/env python3
"""Ejercicio 7: lee mensajes de un named pipe (FIFO).

Uso: python3 lector_fifo.py [ruta_fifo]   (por defecto /tmp/mi_canal)
"""
import os
import sys


def main():
    fifo = sys.argv[1] if len(sys.argv) > 1 else "/tmp/mi_canal"
    if not os.path.exists(fifo):
        os.mkfifo(fifo)  # así da igual cuál de los dos se lanza primero

    print(f"Leyendo de {fifo}...", flush=True)
    # open() se bloquea hasta que haya un escritor
    with open(fifo, "r") as f:
        for linea in f:
            print(f"Recibido: {linea.strip()}", flush=True)

    print("Lectura completada (el escritor cerró el pipe)")


if __name__ == "__main__":
    main()
