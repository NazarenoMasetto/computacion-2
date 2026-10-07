#!/usr/bin/env python3
"""Ej 3 parte C: framing por prefijo de longitud (4 bytes, big-endian).

Uso:
    python3 ej3_framing_longitud.py servidor [--port 8080]
    python3 ej3_framing_longitud.py cliente  [--port 8080] --modo juntos|bytes|newline|vacio
"""
import argparse
import socket
import struct
import time


def recibir_exacto(sock, n):
    """Lee EXACTAMENTE n bytes, o None si cerraron antes.

    recv(n) puede devolver menos de n, así que hay que insistir.
    """
    datos = b''
    while len(datos) < n:
        pedazo = sock.recv(n - len(datos))
        if not pedazo:
            return None
        datos += pedazo
    return datos


def enviar_mensaje(sock, payload: bytes):
    """Cabecera '!I' (4 bytes, orden de red) + contenido."""
    sock.sendall(struct.pack('!I', len(payload)) + payload)


def recibir_mensaje(sock):
    """Devuelve el payload completo, o None si el otro lado cerró."""
    cabecera = recibir_exacto(sock, 4)
    if cabecera is None:
        return None
    (longitud,) = struct.unpack('!I', cabecera)
    if longitud == 0:
        return b''      # mensaje vacío válido (ojo: no confundir con None)
    return recibir_exacto(sock, longitud)


def servidor(puerto):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as srv:
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind(('0.0.0.0', puerto))
        srv.listen(5)
        print(f'[longitud] escuchando en {puerto}', flush=True)
        while True:
            conn, direc = srv.accept()
            print(f'Conexión desde {direc}', flush=True)
            try:
                with conn:
                    while (msg := recibir_mensaje(conn)) is not None:
                        print(f'  mensaje ({len(msg)} bytes): {msg[:60]!r}', flush=True)
                        enviar_mensaje(conn, msg.upper())
            except (ConnectionResetError, BrokenPipeError):
                pass
            print(f'  {direc} cerró', flush=True)


def cliente(puerto, modo):
    with socket.create_connection(('localhost', puerto), timeout=5) as s:
        if modo == 'juntos':
            # los tres mensajes armados en un solo sendall()
            mensajes = [b'uno', b'dos', b'tres']
            s.sendall(b''.join(struct.pack('!I', len(m)) + m for m in mensajes))
        elif modo == 'bytes':
            mensajes = [b'hola']
            for b in struct.pack('!I', 4) + b'hola':
                s.sendall(bytes([b]))
                time.sleep(0.2)
        elif modo == 'newline':
            mensajes = [b'linea con\nsalto adentro']
            enviar_mensaje(s, mensajes[0])
        else:
            mensajes = [b'', b'despues del vacio']
            for m in mensajes:
                enviar_mensaje(s, m)
        s.shutdown(socket.SHUT_WR)
        respuestas = []
        while (r := recibir_mensaje(s)) is not None:
            respuestas.append(r)
    ok = respuestas == [m.upper() for m in mensajes]
    print(f'Respuestas: {respuestas}  -> {"OK" if ok else "ERROR"}')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('rol', choices=['servidor', 'cliente'])
    ap.add_argument('--port', type=int, default=8080)
    ap.add_argument('--modo', choices=['juntos', 'bytes', 'newline', 'vacio'],
                    default='juntos')
    args = ap.parse_args()
    if args.rol == 'servidor':
        servidor(args.port)
    else:
        cliente(args.port, args.modo)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('\nCortado')
