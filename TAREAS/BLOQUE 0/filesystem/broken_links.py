import argparse
import os


def buscar_links_rotos(directorio):
    rotos = []

    for raiz, directorios, archivos in os.walk(directorio):
        for nombre in directorios + archivos:
            ruta = os.path.join(raiz, nombre)
            if os.path.islink(ruta) and not os.path.exists(ruta):
                rotos.append(ruta)

    return rotos


def main():
    parser = argparse.ArgumentParser(description="Busca enlaces simbólicos rotos.")
    parser.add_argument("directorio", help="Directorio donde buscar")
    parser.add_argument("--quiet", action="store_true", help="Muestra solo la cantidad")
    args = parser.parse_args()

    rotos = buscar_links_rotos(args.directorio)

    if args.quiet:
        print(len(rotos))
    else:
        if rotos:
            print("Enlaces rotos encontrados:")
            for ruta in rotos:
                print(ruta)
            print(f"Total: {len(rotos)}")
        else:
            print("No se encontraron enlaces rotos.")


if __name__ == "__main__":
    main()