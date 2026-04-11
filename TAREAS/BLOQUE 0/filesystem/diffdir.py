import argparse
import os


def listar_contenido(directorio):
    try:
        return set(os.listdir(directorio))
    except OSError:
        return None


def main():
    parser = argparse.ArgumentParser(description="Compara dos directorios.")
    parser.add_argument("dir1", help="Primer directorio")
    parser.add_argument("dir2", help="Segundo directorio")
    args = parser.parse_args()

    contenido1 = listar_contenido(args.dir1)
    contenido2 = listar_contenido(args.dir2)

    if contenido1 is None or contenido2 is None:
        print("Error: no se pudo leer uno de los directorios.")
        return

    solo_en_1 = sorted(contenido1 - contenido2)
    solo_en_2 = sorted(contenido2 - contenido1)
    en_ambos = sorted(contenido1 & contenido2)

    print(f"Solo en {args.dir1}:")
    for item in solo_en_1:
        print(f"  {item}")

    print(f"\nSolo en {args.dir2}:")
    for item in solo_en_2:
        print(f"  {item}")

    print("\nEn ambos:")
    for item in en_ambos:
        print(f"  {item}")


if __name__ == "__main__":
    main()