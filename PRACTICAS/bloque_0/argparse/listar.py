import argparse
import os


def main():
    parser = argparse.ArgumentParser(description="Lista archivos de un directorio.")
    parser.add_argument("directorio", nargs="?", default=".", help="Directorio a listar")
    parser.add_argument("-a", "--all", action="store_true", help="Incluye ocultos")
    parser.add_argument("--extension", help="Filtra por extensión")
    args = parser.parse_args()

    try:
        elementos = os.listdir(args.directorio)
    except FileNotFoundError:
        print("Error: directorio no encontrado")
        return
    except OSError:
        print("Error: no se pudo abrir el directorio")
        return

    for nombre in sorted(elementos):
        if not args.all and nombre.startswith("."):
            continue

        ruta = os.path.join(args.directorio, nombre)

        if args.extension and not nombre.endswith(args.extension):
            continue

        if os.path.isdir(ruta):
            print(f"{nombre}/")
        else:
            print(nombre)


if __name__ == "__main__":
    main()