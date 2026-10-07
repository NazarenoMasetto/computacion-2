#!/usr/bin/env python3
"""Ej 3 parte B: framing por delimitador (\\n). Responde en mayúsculas.

Uso:
    python3 ej3_framing_lineas.py servidor [--port 8080]
    python3 ej3_framing_lineas.py cliente  [--port 8080] --modo juntos|bytes|newline

Modos del cliente:
    juntos   manda b'uno\\ndos\\ntres\\n' en un solo sendall() (punto 4)
    bytes    manda b'hola\\n' de a un byte con sleep(0.2)      (punto 5)
    newline  manda un mensaje con \\n en el medio              (punto 7)
"""
import argparse
import socket
import time


def recibir_lineas(sock):
    """Generador de líneas completas (sin el \\n).

    El buffer sobrevive entre recv(): puede llegar media línea o
    tres líneas y media.
    """
    buffer = b''
    while True:
        pedazo = sock.recv(4096)
        if not pedazo:
            if buffer:
                print(f'  (descarto línea incompleta: {buffer!r})')
            return
        buffer += pedazo
        # entregar TODAS las líneas completas que haya
        while b'\n' in buffer:
            linea, buffer = buffer.split(b'\n', 1)
            yield linea


def servidor(puerto):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as srv:
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind(('0.0.0.0', puerto))
        srv.listen(5)
        print(f'[lineas] escuchando en {puerto}', flush=True)
        while True:
            conn, direc = srv.accept()
            print(f'Conexión desde {direc}', flush=True)
            try:
                with conn:
                    for linea in recibir_lineas(conn):
                        print(f'  línea: {linea!r}', flush=True)
                        conn.sendall(linea.upper() + b'\n')
            except (ConnectionResetError, BrokenPipeError):
                pass
            print(f'  {direc} cerró', flush=True)


def cliente(puerto, modo):
    with socket.create_connection(('localhost', puerto), timeout=5) as s:
        if modo == 'juntos':
            s.sendall(b'uno\ndos\ntres\n')
            esperadas = 3
        elif modo == 'bytes':
            for b in b'hola\n':
                s.sendall(bytes([b]))
                time.sleep(0.2)
            esperadas = 1
        else:
            # con delimitador, el \n del medio corta el mensaje en dos
            s.sendall(b'linea con\nsalto adentro\n')
            esperadas = 2
        s.shutdown(socket.SHUT_WR)
        respuestas = list(recibir_lineas(s))
    print(f'Respuestas ({len(respuestas)}, esperaba {esperadas}): {respuestas}')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('rol', choices=['servidor', 'cliente'])
    ap.add_argument('--port', type=int, default=8080)
    ap.add_argument('--modo', choices=['juntos', 'bytes', 'newline'], default='juntos')
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
