#!/usr/bin/env python3
"""Ejercicio 2.1: redirección manual de stdout a un archivo con dup/dup2.

Uso: python3 ej2_1_redireccion_dup2.py [archivo]   (por defecto /tmp/salida.txt)
"""
import os
import sys
import tempfile


def main():
    destino = sys.argv[1] if len(sys.argv) > 1 else os.path.join(tempfile.gettempdir(), "salida.txt")

    print("Este mensaje va a la terminal")
    sys.stdout.flush()  # importante: vaciar el buffer ANTES de cambiar el fd 1

    # Guardar una copia del stdout original
    stdout_original = os.dup(1)

    # Abrir archivo destino y ponerlo en el fd 1
    archivo = os.open(destino, os.O_CREAT | os.O_WRONLY | os.O_TRUNC, 0o644)
    os.dup2(archivo, 1)
    os.close(archivo)  # ya no hace falta, el fd 1 apunta al archivo

    print("Este mensaje va al archivo")
    print("Y este también")
    sys.stdout.flush()  # sin esto, el texto quedaría en el buffer y saldría por la terminal

    # Restaurar stdout
    os.dup2(stdout_original, 1)
    os.close(stdout_original)

    print("Volvimos a la terminal")
    print(f"Revisá el contenido de {destino}")


if __name__ == "__main__":
    main()
