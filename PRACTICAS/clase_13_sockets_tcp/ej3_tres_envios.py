#!/usr/bin/env python3
"""Ej 3 parte A: tres sendall() seguidos; mirar cuántos recv() hace el server.

Uso (con servidor_eco.py corriendo):
    python3 ej3_tres_envios.py [--port 8080]
"""
import argparse
import socket
import time


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--port', type=int, default=8080)
    args = ap.parse_args()
    with socket.create_connection(('localhost', args.port), timeout=5) as s:
        for msg in (b'HOLA', b'COMO', b'ESTAS'):
            s.sendall(msg)
        time.sleep(0.5)    # dar tiempo al eco
        print(f'Eco recibido: {s.recv(4096)!r}')
        print('Mirá la salida del servidor: ¿cuántos recv() hizo?')


if __name__ == '__main__':
    main()
