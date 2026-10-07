#!/usr/bin/env python3
"""Ej 2.2: la señal de cierre (recv() devuelve b'').

Uso:
    python3 ej2_cierre.py [--port 8080] [--sin-chequeo]

Con --sin-chequeo reproduce el bug: al cerrar el servidor, el bucle
gira sin parar imprimiendo b'' (100% de CPU). Cortar con Ctrl+C.
"""
import argparse
import socket


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--port', type=int, default=8080)
    ap.add_argument('--sin-chequeo', action='store_true')
    args = ap.parse_args()

    with socket.create_connection(('localhost', args.port)) as s:
        s.sendall(b'test\n')
        while True:
            datos = s.recv(4096)
            print(f'recv devolvió: {datos!r}', flush=True)
            if not args.sin_chequeo and not datos:
                # este es el chequeo que faltaba: b'' = EOF, el otro cerró
                print('El servidor cerró la conexión.')
                break


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('\nCortado')
