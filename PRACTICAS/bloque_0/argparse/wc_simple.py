import sys


def main():
    if len(sys.argv) != 2:
        print("Error: Debe especificar un archivo")
        sys.exit(1)

    nombre = sys.argv[1]

    try:
        with open(nombre, "r", encoding="utf-8") as archivo:
            cantidad = sum(1 for _ in archivo)
        print(f"{cantidad} líneas")
    except FileNotFoundError:
        print(f"Error: No se puede leer '{nombre}'")
        sys.exit(1)
    except OSError:
        print(f"Error: No se puede leer '{nombre}'")
        sys.exit(1)


if __name__ == "__main__":
    main()