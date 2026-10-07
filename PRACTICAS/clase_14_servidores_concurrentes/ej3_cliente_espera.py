#!/usr/bin/env python3
"""Ej 3 parte A2, punto 7: cliente que se conecta y avisa cuándo ve el cierre.

(Reemplaza a `nc`, que en la versión OpenBSD no termina al recibir el FIN
mientras su stdin siga abierto, y entonces no se nota nada.)

Uso:
    python3 ej3_cliente_espera.py [--port 8080] [--max 10]
Mientras espera, matá al hijo que lo atiende: ps --ppid <PID_PADRE>
"""
import argparse
import socket
import time


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--port', type=int, default=8080)
    ap.add_argument('--max', type=float, default=10.0, help='segundos de espera')
    args = ap.parse_args()
    with socket.create_connection(('localhost', args.port)) as s:
        s.settimeout(args.max)
        print(f'Conectado desde {s.getsockname()}; esperando...', flush=True)
        inicio = time.monotonic()
        try:
            datos = s.recv(4096)
            print(f'recv -> {datos!r} a los {time.monotonic() - inicio:.1f}s '
                  f'({"el servidor CERRÓ" if not datos else "datos"})')
        except TimeoutError:
            print(f'Pasaron {args.max}s y la conexión sigue abierta (no llegó FIN)')
        except ConnectionResetError:
            print('RST: el servidor cortó la conexión')


if __name__ == '__main__':
    main()
