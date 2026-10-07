#!/usr/bin/env python3
"""Ejercicio 6.2: pipeline echo | grep error | wc -l armado con subprocess."""
import subprocess

TEXTO = """
primera linea
segunda linea con error
tercera linea
otra linea con error
ultima linea
"""


def main():
    echo = subprocess.Popen(["echo", TEXTO], stdout=subprocess.PIPE)
    grep = subprocess.Popen(["grep", "error"], stdin=echo.stdout, stdout=subprocess.PIPE)
    wc = subprocess.Popen(["wc", "-l"], stdin=grep.stdout, stdout=subprocess.PIPE, text=True)

    # Cerrar en el padre las copias de los extremos de lectura: así, si un proceso
    # de más adelante muere, el anterior recibe SIGPIPE en vez de colgarse
    echo.stdout.close()
    grep.stdout.close()

    resultado, _ = wc.communicate()
    echo.wait()
    grep.wait()
    print(f"Líneas con 'error': {resultado.strip()}")


if __name__ == "__main__":
    main()
