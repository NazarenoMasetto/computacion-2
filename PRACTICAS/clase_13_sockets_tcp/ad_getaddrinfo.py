#!/usr/bin/env python3
"""Adicional: getaddrinfo() + probar cada dirección hasta que una conecte.

Es, simplificado, lo que hace socket.create_connection() por dentro.

Uso:
    python3 ad_getaddrinfo.py localhost [--port 8080]
"""
import argparse
import socket


def conectar(host, puerto, timeout=3):
    ultimo_error = None
    # getaddrinfo puede devolver varias direcciones (IPv6 e IPv4)
    for familia, tipo, proto, _canon, direccion in socket.getaddrinfo(
            host, puerto, type=socket.SOCK_STREAM):
        nombre = 'IPv6' if familia == socket.AF_INET6 else 'IPv4'
        print(f'Probando {nombre} {direccion}...', end=' ')
        s = socket.socket(familia, tipo, proto)
        s.settimeout(timeout)
        try:
            s.connect(direccion)
            print('conectó')
            return s
        except OSError as e:
            print(f'falló ({type(e).__name__})')
            ultimo_error = e
            s.close()
    raise ultimo_error or OSError('getaddrinfo no devolvió nada')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('host')
    ap.add_argument('--port', type=int, default=8080)
    args = ap.parse_args()
    try:
        with conectar(args.host, args.port) as s:
            print(f'Conectado: local={s.getsockname()} remoto={s.getpeername()}')
    except OSError as e:
        print(f'Ninguna dirección funcionó: {e}')


if __name__ == '__main__':
    main()
