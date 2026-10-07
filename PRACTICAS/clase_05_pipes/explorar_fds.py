#!/usr/bin/env python3
"""Ejercicio 1.2: explorar los file descriptors del proceso actual."""
import os
import tempfile

# Archivo de prueba en el directorio temporal del sistema (/tmp en Linux)
RUTA_PRUEBA = os.path.join(tempfile.gettempdir(), "test_fd.txt")


def listar_fds():
    """Lista los file descriptors abiertos leyendo /proc/<pid>/fd."""
    fd_dir = f"/proc/{os.getpid()}/fd"
    print(f"File descriptors de PID {os.getpid()}:")
    for fd in sorted(os.listdir(fd_dir), key=int):
        try:
            target = os.readlink(f"{fd_dir}/{fd}")
            print(f"  fd {fd} -> {target}")
        except OSError as e:
            # El fd que usa listdir para leer el directorio puede cerrarse antes del readlink
            print(f"  fd {fd} -> (error: {e})")


def main():
    print("=== Estado inicial ===")
    listar_fds()

    print("\n=== Después de abrir un archivo ===")
    f = open(RUTA_PRUEBA, "w")
    print(f"Archivo abierto con fd {f.fileno()}")
    listar_fds()

    print("\n=== Después de abrir otro ===")
    f2 = open("/etc/passwd", "r")
    print(f"Segundo archivo con fd {f2.fileno()}")
    listar_fds()

    print("\n=== Después de cerrar el primero ===")
    f.close()
    listar_fds()

    print("\n=== Después de cerrar todo ===")
    f2.close()
    listar_fds()

    os.remove(RUTA_PRUEBA)  # limpiamos


if __name__ == "__main__":
    main()
