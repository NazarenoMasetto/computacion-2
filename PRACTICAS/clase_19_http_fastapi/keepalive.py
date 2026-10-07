#!/usr/bin/env python3
"""Ejercicio adicional: dos pedidos por la misma conexión (keep-alive).

Necesita crudo.py corriendo con protocol_version = 'HTTP/1.1':
    python3 crudo.py servidor --http11

Manda los dos pedidos juntos en un solo sendall (pipelining) y después
separa las dos respuestas usando el Content-Length de cada una: es la
única forma de saber dónde termina la primera y empieza la segunda,
porque la conexión NO se cierra entre medio.

Uso:
    python3 keepalive.py [puerto]      # por defecto 8080
"""
import os
import socket
import sys

PUERTO = int(sys.argv[1]) if len(sys.argv) > 1 else int(os.environ.get('PUERTO', 8080))


def leer_respuesta(archivo):
    """Lee UNA respuesta: headers hasta la línea vacía, cuerpo por Content-Length."""
    estado = archivo.readline().decode().rstrip('\r\n')
    headers = {}
    while (linea := archivo.readline().decode().rstrip('\r\n')):
        k, _, v = linea.partition(':')
        headers[k.strip().lower()] = v.strip()
    cuerpo = archivo.read(int(headers.get('content-length', 0)))
    return estado, headers, cuerpo


def main():
    pedidos = (
        b'GET /primero HTTP/1.1\r\nHost: localhost\r\n\r\n'
        b'POST /segundo HTTP/1.1\r\nHost: localhost\r\n'
        b'Content-Length: 4\r\n\r\nhola'
    )
    with socket.create_connection(('localhost', PUERTO), timeout=5) as s:
        s.sendall(pedidos)                    # los dos de una, sin cerrar
        archivo = s.makefile('rb')
        for i in (1, 2):
            estado, headers, cuerpo = leer_respuesta(archivo)
            if not estado:
                # Con HTTP/1.0 el servidor cierra después de la primera
                print(f'Respuesta {i}: nada, el servidor cerró la conexión '
                      '(¿está en HTTP/1.0? levantalo con --http11)')
                return
            print(f'Respuesta {i}: {estado}')
            print(f'  Content-Length: {headers.get("content-length")}  '
                  f'Connection: {headers.get("connection", "(no dice)")}')
            print(f'  cuerpo: {cuerpo.decode()}')
        # La conexión sigue abierta: un tercer pedido también entra
        s.sendall(b'GET /tercero HTTP/1.1\r\nHost: localhost\r\nConnection: close\r\n\r\n')
        estado, _, cuerpo = leer_respuesta(archivo)
        print(f'Respuesta 3 (misma conexión, ahora con Connection: close): {estado} {cuerpo.decode()}')


if __name__ == '__main__':
    main()
