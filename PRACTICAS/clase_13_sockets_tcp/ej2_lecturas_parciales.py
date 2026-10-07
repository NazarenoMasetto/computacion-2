#!/usr/bin/env python3
"""Ej 2.1: lee la respuesta del eco con un tope de recv() configurable.

Uso:
    python3 ej2_lecturas_parciales.py [--port 8080] [--tope 4]
"""
import argparse
import socket


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--port', type=int, default=8080)
    ap.add_argument('--tope', type=int, default=4, help='tamaño de cada recv()')
    args = ap.parse_args()

    mensaje = b'un mensaje bastante mas largo que cuatro bytes\n'
    with socket.create_connection(('localhost', args.port), timeout=5) as s:
        s.sendall(mensaje)
        s.shutdown(socket.SHUT_WR)   # aviso que no mando más
        recibido = b''
        llamadas = 0
        while True:
            pedazo = s.recv(args.tope)
            if not pedazo:
                break
            llamadas += 1
            print(f'  recv({args.tope}) -> {pedazo!r}')
            recibido += pedazo
    print(f'recv() con datos: {llamadas} veces')
    print(f'Total: {len(recibido)} de {len(mensaje)} bytes; '
          f'{"no se perdió nada" if recibido == mensaje else "FALTAN BYTES"}')


if __name__ == '__main__':
    main()
