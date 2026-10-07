#!/usr/bin/env python3
"""Ejercicio 2.2: demostración de stdout (fd 1) vs stderr (fd 2)."""
import os
import sys


def main():
    # Escribir a stdout
    print("Mensaje normal a stdout")
    sys.stdout.write("Otro mensaje a stdout\n")
    sys.stdout.flush()  # para que el orden con os.write sea el esperado
    os.write(1, b"Y otro mas directo al fd 1\n")

    # Escribir a stderr
    print("Mensaje de error a stderr", file=sys.stderr)
    sys.stderr.write("Otro error a stderr\n")
    sys.stderr.flush()
    os.write(2, b"Error directo al fd 2\n")


if __name__ == "__main__":
    main()
