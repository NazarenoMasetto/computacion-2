#!/usr/bin/env python3
"""Ejercicio 1: primer fork. Padre e hijo muestran su PID y el de su padre."""
import os


def main():
    pid = os.fork()

    if pid == 0:
        # Rama del hijo: fork() devolvió 0
        print(f"Soy el hijo: PID={os.getpid()}, padre={os.getppid()}", flush=True)
        os._exit(0)  # _exit para no ejecutar el código del padre ni limpiar buffers dos veces
    else:
        # Rama del padre: fork() devolvió el PID del hijo
        print(f"Soy el padre: PID={os.getpid()}, mi padre={os.getppid()}, hijo={pid}", flush=True)
        os.waitpid(pid, 0)  # esperamos al hijo antes de terminar
        print("Programa terminado")


if __name__ == "__main__":
    main()
