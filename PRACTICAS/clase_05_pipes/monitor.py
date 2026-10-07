#!/usr/bin/env python3
"""Adicional: monitor de pipe. Deja pasar los datos de stdin a stdout sin
cambiarlos y muestra estadísticas por stderr (para no ensuciar el pipeline).

Uso: cat archivo | python3 monitor.py [cada_n_lineas] | wc -l
"""
import sys
import time


def main():
    cada = int(sys.argv[1]) if len(sys.argv) > 1 else 0  # 0 = solo el resumen final
    total_bytes = 0
    total_lineas = 0
    inicio = time.monotonic()

    entrada = sys.stdin.buffer
    salida = sys.stdout.buffer
    try:
        for linea in entrada:
            salida.write(linea)
            total_bytes += len(linea)
            total_lineas += 1
            if cada and total_lineas % cada == 0:
                print(f"[monitor] {total_bytes} bytes, {total_lineas} líneas...", file=sys.stderr)
        salida.flush()
    except BrokenPipeError:
        print("[monitor] el siguiente comando cerró el pipe", file=sys.stderr)

    duracion = time.monotonic() - inicio
    velocidad = total_bytes / duracion / 1024 if duracion > 0 else 0
    print(f"[monitor] Procesados {total_bytes} bytes, {total_lineas} líneas "
          f"en {duracion:.2f} s ({velocidad:.1f} KiB/s)", file=sys.stderr)


if __name__ == "__main__":
    main()
