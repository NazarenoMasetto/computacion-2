#!/usr/bin/env python3
"""Ejercicio 7: escribe mensajes a un named pipe (FIFO).

Uso: python3 escritor_fifo.py [cantidad] [intervalo_seg] [ruta_fifo]
     (por defecto 10 mensajes, 1 s, /tmp/mi_canal)
"""
import os
import stat
import sys
import time


def main():
    cantidad = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    intervalo = float(sys.argv[2]) if len(sys.argv) > 2 else 1.0
    fifo = sys.argv[3] if len(sys.argv) > 3 else "/tmp/mi_canal"

    # Crear la FIFO si no existe (y verificar que sea una FIFO de verdad)
    if not os.path.exists(fifo):
        os.mkfifo(fifo)
    elif not stat.S_ISFIFO(os.stat(fifo).st_mode):
        sys.exit(f"{fifo} existe y no es una FIFO")

    print(f"Escribiendo a {fifo}...")
    print("(Ejecutá lector_fifo.py en otra terminal)", flush=True)

    # open() se BLOQUEA hasta que alguien abra la FIFO para leer
    try:
        with open(fifo, "w") as f:
            for i in range(cantidad):
                mensaje = f"Mensaje {i}: {time.ctime()}"
                print(f"Enviando: {mensaje}", flush=True)
                f.write(mensaje + "\n")
                f.flush()  # sin flush el lector no ve nada hasta el final
                time.sleep(intervalo)
    except BrokenPipeError:
        print("El lector cerró la FIFO antes de tiempo")
        return

    print("Escritura completada")


if __name__ == "__main__":
    main()
