#!/usr/bin/env python3
"""Ej 5.1: cliente que reintenta con backoff hasta que el servidor aparezca.

Uso:
    python3 ej5_reintentos.py [--port 8080] [--intentos 5]
Lanzalo ANTES que el servidor y levantá servidor_eco.py unos segundos después.
"""
import argparse
import socket
import time


def conectar_con_reintentos(host, puerto, intentos=5, espera_inicial=0.5):
    """Intenta conectar; si lo rechazan espera cada vez el doble."""
    espera = espera_inicial
    for intento in range(1, intentos + 1):
        try:
            s = socket.create_connection((host, puerto), timeout=5)
            print(f'Conectado en el intento {intento}')
            return s
        except ConnectionRefusedError:
            if intento == intentos:
                raise
            print(f'Intento {intento}: rechazado, reintento en {espera:.1f}s')
            time.sleep(espera)
            espera *= 2       # backoff exponencial
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--port', type=int, default=8080)
    ap.add_argument('--intentos', type=int, default=5)
    args = ap.parse_args()
    try:
        with conectar_con_reintentos('localhost', args.port, args.intentos) as s:
            s.sendall(b'hola despues de reintentar\n')
            print(f'Eco: {s.recv(4096)!r}')
    except ConnectionRefusedError:
        print('El servidor nunca apareció.')


if __name__ == '__main__':
    main()
