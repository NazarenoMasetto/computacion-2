#!/usr/bin/env python3
"""Adicional: servidor de archivos con framing por longitud (clase 13).

Protocolo:
    cliente -> "GET <nombre>\\n"
    servidor -> cabecera struct '!BI' (estado, largo) + largo bytes
                estado 0 = OK (bytes = contenido del archivo)
                estado 1 = error (bytes = mensaje de error en UTF-8)

Solo se sirven archivos dentro del directorio indicado con --dir; un nombre
con "../" o una ruta absoluta se rechaza con error, sin caer el servidor.

Uso:
    python3 servidor_archivos.py [--dir .] [--port 8080]
    python3 servidor_archivos.py --get <nombre> [--port 8080]   # cliente
"""
import argparse
import os
import socket
import socketserver
import struct
import sys

CABECERA = struct.Struct('!BI')     # 1 byte estado + 4 bytes largo
OK, ERROR = 0, 1


def recibir_exacto(sock, n):
    """Lee exactamente n bytes (recv puede devolver menos)."""
    datos = b''
    while len(datos) < n:
        parte = sock.recv(n - len(datos))
        if not parte:
            raise ConnectionError('el servidor cerró antes de tiempo')
        datos += parte
    return datos


class HandlerArchivos(socketserver.StreamRequestHandler):
    def enviar(self, estado, cuerpo):
        self.wfile.write(CABECERA.pack(estado, len(cuerpo)) + cuerpo)

    def handle(self):
        for linea in self.rfile:
            partes = linea.decode('utf-8', 'replace').strip().split(maxsplit=1)
            if len(partes) != 2 or partes[0].upper() != 'GET':
                self.enviar(ERROR, b'uso: GET <nombre>')
                continue
            self.enviar(*self.leer_archivo(partes[1]))

    def leer_archivo(self, nombre):
        base = os.path.realpath(self.server.directorio)
        ruta = os.path.realpath(os.path.join(base, nombre))
        # Evita salir del directorio servido (GET ../../etc/passwd)
        if os.path.commonpath([base, ruta]) != base:
            return ERROR, b'acceso denegado'
        try:
            with open(ruta, 'rb') as f:
                return OK, f.read()
        except FileNotFoundError:
            return ERROR, f'no existe: {nombre}'.encode()
        except (IsADirectoryError, PermissionError) as e:
            return ERROR, f'no se puede leer: {e.strerror}'.encode()


class Servidor(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True

    def __init__(self, direccion, handler, directorio):
        super().__init__(direccion, handler)
        self.directorio = directorio


def cliente(nombre, puerto):
    with socket.create_connection(('localhost', puerto), timeout=10) as s:
        s.sendall(f'GET {nombre}\n'.encode())
        estado, largo = CABECERA.unpack(recibir_exacto(s, CABECERA.size))
        cuerpo = recibir_exacto(s, largo)
    if estado == OK:
        sys.stdout.buffer.write(cuerpo)
        print(f'\n[{largo} bytes recibidos]', file=sys.stderr)
    else:
        print(f'ERROR: {cuerpo.decode()}', file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description='Servidor de archivos')
    parser.add_argument('--dir', default='.', help='directorio a servir')
    parser.add_argument('--port', type=int, default=8080)
    parser.add_argument('--get', metavar='NOMBRE', help='modo cliente')
    args = parser.parse_args()

    if args.get:
        cliente(args.get, args.port)
        return

    with Servidor(('0.0.0.0', args.port), HandlerArchivos, args.dir) as srv:
        print(f'Sirviendo {os.path.realpath(args.dir)} en :{args.port}', flush=True)
        try:
            srv.serve_forever()
        except KeyboardInterrupt:
            print('\nServidor detenido')


if __name__ == '__main__':
    main()
