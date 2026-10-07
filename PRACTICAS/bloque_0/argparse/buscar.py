import argparse
import sys


def procesar_lineas(lineas, patron, ignore_case=False, invert=False):
    coincidencias = []
    patron_comparar = patron.lower() if ignore_case else patron

    for numero, linea in enumerate(lineas, start=1):
        contenido = linea.rstrip("\n")
        texto_comparar = contenido.lower() if ignore_case else contenido

        encontrado = patron_comparar in texto_comparar
        if invert:
            encontrado = not encontrado

        if encontrado:
            coincidencias.append((numero, contenido))

    return coincidencias


def leer_archivo(nombre_archivo):
    try:
        with open(nombre_archivo, "r", encoding="utf-8") as archivo:
            return archivo.readlines()
    except FileNotFoundError:
        print(f"Error: no se encontró el archivo '{nombre_archivo}'", file=sys.stderr)
        sys.exit(1)
    except OSError:
        print(f"Error: no se pudo leer el archivo '{nombre_archivo}'", file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Busca un patrón de texto en uno o más archivos."
    )
    parser.add_argument("patron", help="Texto a buscar")
    parser.add_argument("archivos", nargs="*", help="Archivos donde buscar")
    parser.add_argument(
        "-i", "--ignore-case",
        action="store_true",
        help="Ignora mayúsculas y minúsculas"
    )
    parser.add_argument(
        "-n", "--line-number",
        action="store_true",
        help="Muestra el número de línea"
    )
    parser.add_argument(
        "-c", "--count",
        action="store_true",
        help="Muestra solo la cantidad de coincidencias"
    )
    parser.add_argument(
        "-v", "--invert",
        action="store_true",
        help="Muestra las líneas que NO coinciden"
    )

    args = parser.parse_args()

    if args.archivos:
        multiples_archivos = len(args.archivos) > 1

        for archivo in args.archivos:
            lineas = leer_archivo(archivo)
            coincidencias = procesar_lineas(
                lineas,
                args.patron,
                ignore_case=args.ignore_case,
                invert=args.invert
            )

            if args.count:
                if multiples_archivos:
                    print(f"{archivo}: {len(coincidencias)}")
                else:
                    print(len(coincidencias))
            else:
                for numero, contenido in coincidencias:
                    salida = ""

                    if multiples_archivos:
                        salida += f"{archivo}:"

                    if args.line_number or multiples_archivos:
                        salida += f"{numero}:"

                    salida += contenido
                    print(salida)
    else:
        if sys.stdin.isatty():
            print("Error: debes indicar un archivo o pasar texto por stdin.", file=sys.stderr)
            sys.exit(1)

        lineas = sys.stdin.readlines()
        coincidencias = procesar_lineas(
            lineas,
            args.patron,
            ignore_case=args.ignore_case,
            invert=args.invert
        )

        if args.count:
            print(len(coincidencias))
        else:
            for numero, contenido in coincidencias:
                if args.line_number:
                    print(f"{numero}:{contenido}")
                else:
                    print(contenido)


if __name__ == "__main__":
    main()