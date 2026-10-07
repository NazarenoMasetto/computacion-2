#!/usr/bin/env python3
"""Ejercicio 5: abrir muchas conexiones simultáneas y dejarlas abiertas.

Abre N conexiones contra el servidor y las mantiene un rato sin hacer
nada, para poder medir threads y memoria del servidor desde otra terminal.

Uso:
    python3 ej5_conexiones.py -n 200 [--port 8080] [--espera 15]
"""
import argparse
import socket
import time


def main():
    parser = argparse.ArgumentParser(description='Conexiones masivas')
    parser.add_argument('-n', type=int, default=200)
    parser.add_argument('--port', type=int, default=8080)
    parser.add_argument('--espera', type=float, default=15,
                        help='segundos que se mantienen abiertas')
    args = parser.parse_args()

    socks = []
    t0 = time.perf_counter()
    for i in range(args.n):
        try:
            s = socket.create_connection(('localhost', args.port), timeout=5)
            socks.append(s)
        except OSError as e:
            print(f'falló la conexión {i + 1}: {e}')
            break
    print(f'{len(socks)} conexiones abiertas en '
          f'{time.perf_counter() - t0:.2f}s; espero {args.espera}s...', flush=True)
    time.sleep(args.espera)
    for s in socks:
        s.close()
    print('cerradas')


if __name__ == '__main__':
    main()
