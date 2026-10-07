#!/usr/bin/env python3
"""Ejercicio 1.1: crear un archivo, mapearlo y modificarlo con mmap."""
import mmap

ARCHIVO = "/tmp/mmap_test.txt"


def main():
    # Crear archivo con contenido
    with open(ARCHIVO, "wb") as f:
        f.write(b"Linea 1: Hola mundo\n")
        f.write(b"Linea 2: Computacion II\n")
        f.write(b"Linea 3: mmap es genial\n")

    # Mapear el archivo (tamaño 0 = todo el archivo)
    with open(ARCHIVO, "r+b") as f:
        mm = mmap.mmap(f.fileno(), 0)

        # Leer todo el contenido
        print("=== Contenido completo ===")
        print(mm[:].decode())

        # Leer línea por línea
        print("=== Línea por línea ===")
        mm.seek(0)
        while True:
            linea = mm.readline()
            if not linea:
                break
            print(f"  {linea.decode().strip()}")

        # Buscar texto. OJO: find() busca desde la posición actual, y después
        # del readline() quedamos al final -> hay que pasarle start=0 (o hacer seek(0))
        pos = mm.find(b"mmap", 0)
        print(f"\n'mmap' encontrado en posición: {pos}")

        # Modificar una parte (mismo largo: mmap no puede cambiar el tamaño)
        mm.seek(pos)
        mm.write(b"MMAP")  # Sobrescribir en mayúsculas

        # Ver resultado
        mm.seek(0)
        print("\n=== Después de modificar ===")
        print(mm[:].decode())

        mm.close()


if __name__ == "__main__":
    main()
