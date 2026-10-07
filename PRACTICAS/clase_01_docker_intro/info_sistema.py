#!/usr/bin/env python3
"""Ejercicio de síntesis: muestra información del sistema donde corre.

Sirve para comparar lo que "ve" Python en el host contra lo que ve
dentro de distintos contenedores (python:3.11, python:3.9, etc.).
Solo usa la biblioteca estándar.
"""

import os
import platform
import sys


def leer_os_release():
    """Devuelve el PRETTY_NAME de /etc/os-release (la distro), si existe."""
    try:
        with open("/etc/os-release") as f:
            for linea in f:
                if linea.startswith("PRETTY_NAME="):
                    return linea.split("=", 1)[1].strip().strip('"')
    except OSError:
        pass
    return "desconocida"


def leer_memoria():
    """Lee MemTotal y MemAvailable de /proc/meminfo (en MB).

    Devuelve None si no estamos en Linux o no se puede leer.
    """
    try:
        datos = {}
        with open("/proc/meminfo") as f:
            for linea in f:
                clave, valor = linea.split(":", 1)
                datos[clave] = int(valor.split()[0])  # viene en kB
        return datos["MemTotal"] // 1024, datos["MemAvailable"] // 1024
    except (OSError, KeyError, ValueError):
        return None


def limite_memoria_cgroup():
    """Si el contenedor tiene límite de memoria (docker run -m), lo muestra.

    cgroup v2 usa memory.max, cgroup v1 usa memory.limit_in_bytes.
    """
    rutas = ["/sys/fs/cgroup/memory.max",
             "/sys/fs/cgroup/memory/memory.limit_in_bytes"]
    for ruta in rutas:
        try:
            with open(ruta) as f:
                valor = f.read().strip()
            if valor == "max" or int(valor) > 2**60:
                return "sin límite"
            return f"{int(valor) // (1024 * 1024)} MB"
        except (OSError, ValueError):
            continue
    return "no disponible"


def main():
    print("=" * 50)
    print("Información del sistema")
    print("=" * 50)

    # Versión de Python
    print(f"Python:            {platform.python_version()} ({platform.python_implementation()})")
    print(f"Ejecutable:        {sys.executable}")

    # Sistema operativo: el kernel es el del host, la distro es la de la imagen
    print(f"Sistema operativo: {platform.system()}")
    print(f"Kernel (release):  {platform.release()}")
    print(f"Distribución:      {leer_os_release()}")
    print(f"Hostname:          {platform.node()}")

    # CPUs: cpu_count() son las del equipo, sched_getaffinity las que puedo usar
    print(f"CPUs (total):      {os.cpu_count()}")
    if hasattr(os, "sched_getaffinity"):
        print(f"CPUs (usables):    {len(os.sched_getaffinity(0))}")

    # Memoria
    mem = leer_memoria()
    if mem:
        print(f"Memoria total:     {mem[0]} MB")
        print(f"Memoria libre:     {mem[1]} MB")
    else:
        print("Memoria:           no se pudo obtener")
    print(f"Límite cgroup:     {limite_memoria_cgroup()}")

    # Variables de entorno que empiezan con PYTHON
    print("\nVariables de entorno PYTHON*:")
    vars_python = {k: v for k, v in os.environ.items() if k.startswith("PYTHON")}
    if vars_python:
        for k in sorted(vars_python):
            print(f"  {k}={vars_python[k]}")
    else:
        print("  (ninguna)")
    print("=" * 50)


if __name__ == "__main__":
    main()
