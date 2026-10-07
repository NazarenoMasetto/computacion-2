#!/usr/bin/env python3
"""Adicional: eco con selectors y timeout de inactividad.

Cada cliente guarda la hora de su última actividad. El select() se llama
con timeout para que el loop despierte aunque nadie mande nada, y en cada
vuelta se desconecta a los que superaron el límite.

Uso:
    python3 servidor_timeout.py [--timeout 30] [--port 8080]
    nc localhost 8080        (y no escribas nada)
"""
import argparse
import selectors
import socket
import time

sel = selectors.DefaultSelector()
ultima_actividad = {}           # socket -> time.monotonic() del último dato


def cerrar(conn, motivo):
    sel.unregister(conn)
    ultima_actividad.pop(conn, None)
    conn.close()
    print(f'- cliente ({motivo})', flush=True)


def revisar_inactivos(limite):
    ahora = time.monotonic()
    for conn, t in list(ultima_actividad.items()):
        if ahora - t > limite:
            try:
                conn.send(b'Desconectado por inactividad\n')
            except OSError:
                pass
            cerrar(conn, 'timeout')


def main():
    parser = argparse.ArgumentParser(description='selectors con timeout')
    parser.add_argument('--timeout', type=float, default=30)
    parser.add_argument('--port', type=int, default=8080)
    args = parser.parse_args()

    servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    servidor.bind(('0.0.0.0', args.port))
    servidor.listen(128)
    servidor.setblocking(False)
    sel.register(servidor, selectors.EVENT_READ)
    print(f'Escuchando en :{args.port} (timeout {args.timeout}s)', flush=True)

    # Despertar seguido para no pasarse mucho del límite
    intervalo = min(1.0, args.timeout / 2)
    try:
        while True:
            # Si vence el timeout, select() devuelve [] y vamos a revisar
            for clave, _ in sel.select(timeout=intervalo):
                if clave.fileobj is servidor:
                    conn, direccion = servidor.accept()
                    conn.setblocking(False)
                    sel.register(conn, selectors.EVENT_READ)
                    ultima_actividad[conn] = time.monotonic()
                    print(f'+ cliente {direccion}', flush=True)
                    continue
                conn = clave.fileobj
                try:
                    datos = conn.recv(4096)
                except ConnectionResetError:
                    datos = b''
                if datos:
                    ultima_actividad[conn] = time.monotonic()
                    conn.sendall(datos)
                else:
                    cerrar(conn, 'cerró')
            revisar_inactivos(args.timeout)
    except KeyboardInterrupt:
        print('\nServidor detenido')
    finally:
        sel.close()


if __name__ == '__main__':
    main()
