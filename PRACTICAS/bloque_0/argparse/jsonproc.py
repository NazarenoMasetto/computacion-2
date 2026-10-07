import argparse
import json
import sys


def cargar_json(ruta):
    try:
        with open(ruta, "r", encoding="utf-8") as archivo:
            return json.load(archivo)
    except FileNotFoundError:
        print(f"Error: no se encontró '{ruta}'")
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"Error: '{ruta}' no contiene JSON válido")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Procesa archivos JSON simples.")
    parser.add_argument("archivo", help="Archivo JSON a leer")
    parser.add_argument("--key", help="Clave a mostrar")
    parser.add_argument("--keys", action="store_true", help="Mostrar todas las claves")
    args = parser.parse_args()

    datos = cargar_json(args.archivo)

    if not isinstance(datos, dict):
        print("Error: el JSON debe ser un objeto/diccionario en la raíz")
        sys.exit(1)

    if args.keys:
        for clave in datos.keys():
            print(clave)
    elif args.key:
        if args.key in datos:
            print(datos[args.key])
        else:
            print(f"Error: la clave '{args.key}' no existe")
            sys.exit(1)
    else:
        print(json.dumps(datos, indent=4, ensure_ascii=False))


if __name__ == "__main__":
    main()