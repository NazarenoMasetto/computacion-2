#!/usr/bin/env python3
"""Ej 5: descubrimiento por broadcast (DISCOVER? -> nombre de la máquina).

Uso:
    python3 ej5_broadcast.py servidor [--port 8082]
    python3 ej5_broadcast.py cliente  [--port 8082] [--sin-permiso] [--destino 255.255.255.255]
"""
import argparse
import socket


def servidor(puerto):
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(('', puerto))        # '' = todas las interfaces (incluye broadcast)
        print(f'Esperando DISCOVER? en el puerto {puerto}', flush=True)
        while True:
            datos, origen = s.recvfrom(4096)
            print(f'  {datos!r} de {origen}', flush=True)
            if datos.strip() == b'DISCOVER?':
                s.sendto(f'AQUI {socket.gethostname()}'.encode(), origen)


def cliente(puerto, destino, con_permiso):
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        if con_permiso:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        s.settimeout(2.0)
        try:
            s.sendto(b'DISCOVER?', (destino, puerto))
        except PermissionError as e:
            print(f'PermissionError: {e}  (falta SO_BROADCAST)')
            return
        except OSError as e:
            print(f'OSError al enviar: {e}  (¿hay ruta para broadcast en esta máquina?)')
            return
        respuestas = []
        try:
            while True:            # puede contestar más de una máquina
                datos, origen = s.recvfrom(4096)
                respuestas.append((origen, datos))
                print(f'{origen} respondió: {datos!r}')
        except TimeoutError:
            pass
        if not respuestas:
            print('Nadie respondió')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('rol', choices=['servidor', 'cliente'])
    ap.add_argument('--port', type=int, default=8082)
    ap.add_argument('--destino', default='255.255.255.255')
    ap.add_argument('--sin-permiso', action='store_true')
    args = ap.parse_args()
    if args.rol == 'servidor':
        servidor(args.port)
    else:
        cliente(args.port, args.destino, not args.sin_permiso)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('\nCortado')
