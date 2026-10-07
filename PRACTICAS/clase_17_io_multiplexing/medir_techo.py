#!/usr/bin/env python3
"""Adicional: medir el techo real de un servidor con selectors.

Abre conexiones contra el servidor hasta que algo falle (o hasta --max),
las deja abiertas unos segundos y muestra cuántas llegó a abrir y el
límite de descriptores del proceso (ulimit -n).

Uso:
    python3 medir_techo.py [--port 8080] [--max 20000] [--espera 5]
"""
import argparse
import resource
import socket
import time


def main():
    parser = argparse.ArgumentParser(description='Medir el techo de conexiones')
    parser.add_argument('--port', type=int, default=8080)
    parser.add_argument('--max', type=int, default=20000)
    parser.add_argument('--espera', type=float, default=5)
    args = parser.parse_args()

    blando, duro = resource.getrlimit(resource.RLIMIT_NOFILE)
    print(f'ulimit -n de este cliente: {blando} (duro: {duro})')

    socks = []
    t0 = time.perf_counter()
    try:
        for _ in range(args.max):
            socks.append(socket.create_connection(('localhost', args.port), timeout=5))
    except OSError as e:
        print(f'falló al abrir la conexión {len(socks) + 1}: {e}')
    print(f'{len(socks)} conexiones abiertas en {time.perf_counter() - t0:.2f}s',
          flush=True)
    time.sleep(args.espera)
    for s in socks:
        s.close()


if __name__ == '__main__':
    main()
