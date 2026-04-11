import argparse
import os


def parsear_tamano(texto):
    texto = texto.strip().upper()

    if texto.endswith("K"):
        return int(float(texto[:-1]) * 1024)
    if texto.endswith("M"):
        return int(float(texto[:-1]) * 1024 * 1024)
    if texto.endswith("G"):
        return int(float(texto[:-1]) * 1024 * 1024 * 1024)

    return int(texto)


def formatear_tamano(bytes_size):
    if bytes_size >= 1024 * 1024 * 1024:
        return f"{bytes_size / (1024 * 1024 * 1024):.1f} GB"
    if bytes_size >= 1024 * 1024:
        return f"{bytes_size / (1024 * 1024):.1f} MB"
    if bytes_size >= 1024:
        return f"{bytes_size / 1024:.1f} KB"
    return f"{bytes_size} B"


def buscar_elementos(directorio, min_size, tipo=None):
    resultados = []

    for raiz, directorios, archivos in os.walk(directorio):
        if tipo in (None, "d"):
            for nombre in directorios:
                ruta = os.path.join(raiz, nombre)
                try:
                    tamano = os.path.getsize(ruta)
                    if tamano >= min_size:
                        resultados.append((ruta, tamano))
                except OSError:
                    pass

        if tipo in (None, "f"):
            for nombre in archivos:
                ruta = os.path.join(raiz, nombre)
                try:
                    tamano = os.path.getsize(ruta)
                    if tamano >= min_size:
                        resultados.append((ruta, tamano))
                except OSError:
                    pass

    return resultados


def main():
    parser = argparse.ArgumentParser(
        description="Busca archivos o directorios grandes."
    )
    parser.add_argument("directorio", help="Directorio donde buscar")
    parser.add_argument(
        "--min-size",
        required=True,
        help="Tamaño mínimo (ej: 100K, 1M, 2G)"
    )
    parser.add_argument(
        "--type",
        choices=["f", "d"],
        help="f = archivos, d = directorios"
    )
    parser.add_argument(
        "--top",
        type=int,
        help="Muestra solo los N más grandes"
    )

    args = parser.parse_args()

    try:
        min_size = parsear_tamano(args.min_size)
    except ValueError:
        print("Error: tamaño mínimo inválido.")
        return

    if not os.path.isdir(args.directorio):
        print("Error: el directorio no existe.")
        return

    resultados = buscar_elementos(args.directorio, min_size, args.type)
    resultados.sort(key=lambda x: x[1], reverse=True)

    if args.top:
        resultados = resultados[:args.top]

    total_archivos = len(resultados)
    total_bytes = sum(tamano for _, tamano in resultados)

    if args.top:
        print(f"Los {len(resultados)} elementos más grandes:")

    for ruta, tamano in resultados:
        print(f"{ruta} ({formatear_tamano(tamano)})")

    print(f"Total: {total_archivos} elementos, {formatear_tamano(total_bytes)}")


if __name__ == "__main__":
    main()