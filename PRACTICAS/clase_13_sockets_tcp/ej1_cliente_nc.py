#!/usr/bin/env python3
"""Ej 1.1: cliente TCP mínimo para probar contra `nc -l 8080`.

Uso:
    python3 ej1_cliente_nc.py [--port 8080] [--sin-recv]
"""
import argparse
import socket


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--host', default='localhost')
    ap.add_argument('--port', type=int, default=8080)
    ap.add_argument('--sin-recv', action='store_true',
                    help='no esperar respuesta (punto 3)')
    args = ap.parse_args()

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((args.host, args.port))
        s.sendall(b'hola desde Python\n')
        if not args.sin_recv:
            # recv() se bloquea hasta que nc mande algo (o cierre)
            print(f'Recibido: {s.recv(4096)!r}')
        else:
            print('Enviado; cierro sin leer nada.')


if __name__ == '__main__':
    main()
