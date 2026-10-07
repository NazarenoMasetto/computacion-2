#!/usr/bin/env python3
"""Ejercicio adicional: cliente HTTP a mano, sin requests ni httpx.

Abre un socket, manda un GET y separa la respuesta en línea de estado,
headers y cuerpo. Para saber dónde termina el cuerpo:
    - si viene Content-Length, se leen exactamente esos bytes;
    - si viene Transfer-Encoding: chunked, se decodifican los pedazos;
    - si no viene ninguno, el cuerpo es todo hasta que el servidor cierra.

Uso:
    python3 cliente_http.py http://localhost:8080/hola
    python3 cliente_http.py http://example.com/
"""
import socket
import sys
from urllib.parse import urlsplit


def leer_linea(archivo):
    """Lee una línea terminada en \\r\\n (o \\n) y la devuelve sin el final."""
    return archivo.readline().rstrip(b'\r\n')


def leer_chunked(archivo):
    """Cada pedazo es: tamaño en hex \\r\\n datos \\r\\n. Termina con tamaño 0."""
    cuerpo = b''
    while True:
        tam = int(leer_linea(archivo).split(b';')[0], 16)
        if tam == 0:
            # puede haber headers finales (trailers) hasta la línea vacía
            while leer_linea(archivo):
                pass
            return cuerpo
        cuerpo += archivo.read(tam)
        archivo.read(2)                       # el \r\n después de cada pedazo


def get(url):
    """Hace un GET y devuelve (linea_estado, headers, cuerpo)."""
    partes = urlsplit(url)
    if partes.scheme != 'http':
        raise ValueError('solo http:// (https necesita TLS)')
    host = partes.hostname
    puerto = partes.port or 80
    ruta = partes.path or '/'
    if partes.query:
        ruta += '?' + partes.query

    pedido = (
        f'GET {ruta} HTTP/1.1\r\n'
        f'Host: {host}\r\n'
        f'User-Agent: cliente-a-mano/0.1\r\n'
        f'Connection: close\r\n'
        f'\r\n'
    )
    with socket.create_connection((host, puerto), timeout=10) as s:
        s.sendall(pedido.encode())
        # makefile nos da readline() y read(n) con buffer: framing fácil
        archivo = s.makefile('rb')

        linea_estado = leer_linea(archivo).decode('latin-1')

        # Headers: hasta la línea vacía (framing por delimitador)
        headers = {}
        while True:
            linea = leer_linea(archivo)
            if not linea:
                break
            nombre, _, valor = linea.decode('latin-1').partition(':')
            headers[nombre.strip().lower()] = valor.strip()

        # Cuerpo: según lo que digan los headers
        if 'content-length' in headers:
            cuerpo = archivo.read(int(headers['content-length']))
        elif headers.get('transfer-encoding', '').lower() == 'chunked':
            cuerpo = leer_chunked(archivo)
        else:
            cuerpo = archivo.read()          # sin largo: hasta que cierre
        archivo.close()

    return linea_estado, headers, cuerpo


def main():
    url = sys.argv[1] if len(sys.argv) > 1 else 'http://localhost:8080/hola'
    estado, headers, cuerpo = get(url)
    version, codigo, *texto = estado.split(' ', 2)
    print(f'Línea de estado: {estado}')
    print(f'  versión={version} código={codigo} texto={" ".join(texto)}')
    print('Headers:')
    for k, v in headers.items():
        print(f'  {k}: {v}')
    modo = ('Content-Length' if 'content-length' in headers else
            'chunked' if 'transfer-encoding' in headers else
            'hasta el cierre (sin Content-Length)')
    print(f'Cuerpo ({len(cuerpo)} bytes, delimitado por {modo}):')
    print(cuerpo.decode('utf-8', 'replace')[:500])


if __name__ == '__main__':
    main()
