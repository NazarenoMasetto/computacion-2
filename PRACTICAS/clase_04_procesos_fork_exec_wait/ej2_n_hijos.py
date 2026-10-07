#!/usr/bin/env python3
"""Ejercicio 2: crear N hijos, cada uno duerme un rato y sale con su número."""
import os
import random
import sys
import time


def main(n=5):
    hijos = []
    for i in range(n):
        pid = os.fork()
        if pid == 0:
            # Reinicio la semilla para que cada hijo no herede la misma secuencia
            random.seed()
            duracion = random.uniform(0.5, 2)
            print(f"[Hijo {i}] PID={os.getpid()}, duermo {duracion:.2f}s", flush=True)
            time.sleep(duracion)
            os._exit(i)  # el código de salida es el número de hijo
        hijos.append((pid, i))

    # El padre espera a todos (en orden de creación)
    for pid, i in hijos:
        _, status = os.waitpid(pid, 0)
        print(f"Hijo {i} (PID {pid}) terminó con código {os.WEXITSTATUS(status)}")


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 5)
