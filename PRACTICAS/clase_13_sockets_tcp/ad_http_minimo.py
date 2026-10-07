#!/usr/bin/env python3
"""Adicional: cliente HTTP/1.1 mínimo a mano (sin requests ni http.client).

Uso:
    python3 ad_http_minimo.py example.com [--port 80] [--path /]
    # prueba local: python3 -m http.server 8080 & python3 ad_http_minimo.py localhost --port 8080
"""
import argparse
import socket


def leer_todo(sock):
    """Lee hasta que el servidor cierre (pedimos Connection: close)."""
    partes = []
    while (pedazo := sock.recv(4096)):
        partes.append(pedazo)
    return b''.join(partes)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('host')
    ap.add_argument('--port', type=int, default=80)
    ap.add_argument('--path', default='/')
    args = ap.parse_args()

    peticion = (f'GET {args.path} HTTP/1.1\r\n'
                f'Host: {args.host}\r\n'
                f'User-Agent: compu2-cliente-minimo\r\n'
                f'Connection: close\r\n\r\n')
    with socket.create_connection((args.host, args.port), timeout=10) as s:
        s.sendall(peticion.encode('ascii'))
        crudo = leer_todo(s)

    # headers y cuerpo están separados por una línea vacía (\r\n\r\n)
    cabecera, _, cuerpo = crudo.partition(b'\r\n\r\n')
    lineas = cabecera.decode('iso-8859-1').split('\r\n')
    version, codigo, motivo = lineas[0].split(' ', 2)
    headers = {}
    for linea in lineas[1:]:
        nombre, _, valor = linea.partition(':')
        headers[nombre.strip().lower()] = valor.strip()

    print(f'Status: {codigo} {motivo} ({version})')
    for k, v in headers.items():
        print(f'  {k}: {v}')
    if 'content-length' in headers:
        print(f'Content-Length dice {headers["content-length"]}, recibí {len(cuerpo)} bytes')
    print('--- primeros 300 bytes del cuerpo ---')
    print(cuerpo[:300].decode('utf-8', errors='replace'))


if __name__ == '__main__':
    main()
