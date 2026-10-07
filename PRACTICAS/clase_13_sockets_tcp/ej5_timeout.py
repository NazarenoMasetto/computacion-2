#!/usr/bin/env python3
"""Ej 5.1 (punto 1) y 5.2: conexión rechazada y recv() con/sin timeout.

Uso:
    python3 ej5_timeout.py [--port 8080] [--timeout 3]
    python3 ej5_timeout.py --timeout 0      # sin timeout: se cuelga (Ctrl+C)
"""
import argparse
import socket


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--port', type=int, default=8080)
    ap.add_argument('--timeout', type=float, default=3.0)
    args = ap.parse_args()
    try:
        with socket.create_connection(('localhost', args.port)) as s:
            if args.timeout > 0:
                s.settimeout(args.timeout)
            print('Conectado; no mando nada y espero con recv()...', flush=True)
            datos = s.recv(4096)    # el eco no manda nada si yo no mando
            print(f'recv -> {datos!r}')
    except ConnectionRefusedError as e:
        print(f'ConnectionRefusedError: {e}')
    except TimeoutError as e:
        print(f'TimeoutError: {e} (pasaron {args.timeout}s sin datos)')


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('\nCortado (sin timeout, recv() esperaba para siempre)')
