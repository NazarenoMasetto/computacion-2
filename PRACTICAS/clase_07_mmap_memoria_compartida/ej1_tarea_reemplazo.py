#!/usr/bin/env python3
"""
Tarea 1: crear un archivo de 5 líneas, buscar una palabra con mmap.find()
y reemplazarla por otra del mismo largo. Después verificar con `cat`.

Uso: python3 ej1_tarea_reemplazo.py [archivo] [buscar] [reemplazo]
     (default: /tmp/mmap_tarea.txt  clave  CLAVE)
"""
import mmap
import sys

LINEAS = [
    "Esta es la primera línea del archivo de ejemplo.",
    "Esta es la segunda línea con la palabra clave.",
    "Tercera línea para tener algo de contenido.",
    "Cuarta línea con números: 12345 67890.",
    "Quinta línea final del archivo.",
]


def main():
    archivo = sys.argv[1] if len(sys.argv) > 1 else "/tmp/mmap_tarea.txt"
    buscar = (sys.argv[2] if len(sys.argv) > 2 else "clave").encode()
    reemplazo = (sys.argv[3] if len(sys.argv) > 3 else "CLAVE").encode()

    # mmap no puede agrandar ni achicar el archivo: el reemplazo tiene que medir lo mismo
    if len(buscar) != len(reemplazo):
        print("Error: la palabra y el reemplazo tienen que tener el mismo largo (en bytes)")
        sys.exit(1)

    with open(archivo, "w", encoding="utf-8") as f:
        f.write("\n".join(LINEAS) + "\n")

    with open(archivo, "r+b") as f:
        with mmap.mmap(f.fileno(), 0) as mm:
            pos = mm.find(buscar)
            if pos == -1:
                print(f"No se encontró {buscar.decode()!r}")
                sys.exit(1)
            print(f"{buscar.decode()!r} encontrada en el byte {pos}")
            mm[pos:pos + len(reemplazo)] = reemplazo
            mm.flush()  # forzar que los cambios lleguen al archivo en disco

    print(f"Reemplazada por {reemplazo.decode()!r}. Verificá con: cat {archivo}")


if __name__ == "__main__":
    main()
