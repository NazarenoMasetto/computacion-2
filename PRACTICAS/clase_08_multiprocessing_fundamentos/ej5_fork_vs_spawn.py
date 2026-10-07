#!/usr/bin/env python3
"""Ejercicio 5: comparar el tiempo de creación de 100 procesos con fork y con spawn.

Uso:
  python3 ej5_fork_vs_spawn.py             -> corre el mismo programa con cada método y compara
  python3 ej5_fork_vs_spawn.py spawn       -> solo un método (fork | spawn | forkserver)
  python3 ej5_fork_vs_spawn.py fork 200    -> otra cantidad de procesos
"""
import multiprocessing
import subprocess
import sys
import time


def tarea_vacia():
    """El hijo no hace nada: así medimos solo el costo de crear el proceso."""
    pass


def medir(metodo, n):
    """Crea n procesos con el método dado y devuelve (t_start, t_total)."""
    multiprocessing.set_start_method(metodo)  # solo se puede llamar UNA vez por programa

    inicio = time.perf_counter()
    procesos = [multiprocessing.Process(target=tarea_vacia) for _ in range(n)]
    for p in procesos:
        p.start()
    t_start = time.perf_counter() - inicio
    for p in procesos:
        p.join()
    t_total = time.perf_counter() - inicio
    return t_start, t_total


def main():
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 100

    if len(sys.argv) > 1:
        metodo = sys.argv[1]
        t_start, t_total = medir(metodo, n)
        print(f"{metodo:>10}: {n} procesos -> start() {t_start:.3f} s | "
              f"start+join {t_total:.3f} s | {t_total / n * 1000:.2f} ms/proceso")
        return

    # Sin argumentos: relanzo ESTE mismo script una vez por método, porque
    # set_start_method no se puede cambiar dentro del mismo proceso
    for metodo in ("fork", "spawn"):
        subprocess.run([sys.executable, __file__, metodo, str(n)], check=True)


if __name__ == "__main__":
    main()
