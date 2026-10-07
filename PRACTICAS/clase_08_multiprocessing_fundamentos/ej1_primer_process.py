#!/usr/bin/env python3
"""Ejercicio 1: el "primer fork" de la clase 4 reescrito con multiprocessing.Process."""
import multiprocessing
import os


def trabajo_hijo():
    """Código que corre en el hijo (equivale a la rama `if pid == 0`)."""
    print(f"Soy el hijo: PID={os.getpid()}, padre={os.getppid()}", flush=True)


def main():
    p = multiprocessing.Process(target=trabajo_hijo, name="hijo")
    p.start()  # acá se hace el fork (o spawn) por debajo
    print(f"Soy el padre: PID={os.getpid()}, hijo={p.pid}", flush=True)
    p.join()   # equivale a os.waitpid(pid, 0)
    print(f"El hijo terminó con exitcode={p.exitcode}")
    print("Programa terminado")


if __name__ == "__main__":
    main()
