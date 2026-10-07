#!/usr/bin/env python3
"""Servidor eco TCP secuencial (versión propia, para los ej. 2, 5 y 6).

Uso:
    python3 servidor_eco.py [--port 8080] [--lento SEG] [--backlog N]

--lento   duerme SEG segundos antes de atender a cada cliente (ej. 6)
--backlog tamaño de la cola de listen() (ej. 6.5 usa 1)
"""
import argparse
import socket
import time


def atender(conn, direccion, lento):
    """Devuelve todo lo que mande el cliente hasta que cierre."""
    if lento:
        time.sleep(lento)   # simula trabajo pesado
    total = 0
    while True:
        datos = conn.recv(4096)
        if not datos:       # b'' = el otro lado cerró
            break
        total += len(datos)
        print(f'  [{direccion[0]}:{direccion[1]}] recv {len(datos)} bytes: {datos!r}',
              flush=True)
        conn.sendall(datos)
    print(f'  [{direccion[0]}:{direccion[1]}] cerró tras {total} bytes', flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--port', type=int, default=8080)
    ap.add_argument('--lento', type=float, default=0.0)
    ap.add_argument('--backlog', type=int, default=5)
    args = ap.parse_args()

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as srv:
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind(('0.0.0.0', args.port))
        srv.listen(args.backlog)
        print(f'Escuchando en 0.0.0.0:{args.port} (backlog={args.backlog}, '
              f'lento={args.lento}s)', flush=True)
        while True:
            conn, direccion = srv.accept()
            print(f'Conexión desde {direccion}', flush=True)
            try:
                with conn:
                    atender(conn, direccion, args.lento)
            except (ConnectionResetError, BrokenPipeError) as e:
                # un cliente que corta mal no tiene que tumbar al servidor
                print(f'  [{direccion}] desconexión abrupta: {e}', flush=True)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('\nServidor detenido')
