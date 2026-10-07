#!/usr/bin/env python3
"""Ejercicio 1.1: servidor con polling activo (busy-waiting). Funciona, pero mal.

Sockets no bloqueantes sin select(): el bucle pregunta todo el tiempo
"¿hay algo?" y quema CPU aunque no haya nadie conectado.

Uso:
    python3 ej1_busy_wait.py [--port 8080]
    nc localhost 8080
Medir CPU (otra terminal):  ps -o %cpu= -p <pid>   o   top -p <pid>
"""
import argparse
import os
import socket


def main():
    parser = argparse.ArgumentParser(description='Servidor con busy-waiting')
    parser.add_argument('--port', type=int, default=8080)
    args = parser.parse_args()

    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(('localhost', args.port))
    srv.listen(5)
    srv.setblocking(False)
    print(f'Busy-waiting en :{args.port} (pid {os.getpid()})', flush=True)

    conexiones = []
    try:
        while True:                      # nunca duerme: gira a fondo
            try:
                conn, _ = srv.accept()
                conn.setblocking(False)
                conexiones.append(conn)
            except BlockingIOError:
                pass                     # nadie esperando: seguir girando
            for c in list(conexiones):
                try:
                    datos = c.recv(4096)
                    if datos:
                        c.sendall(datos)
                    else:
                        conexiones.remove(c)
                        c.close()
                except BlockingIOError:
                    pass                 # sin datos: seguir girando
    except KeyboardInterrupt:
        print('\nServidor detenido')
    finally:
        for c in conexiones:
            c.close()
        srv.close()


if __name__ == '__main__':
    main()
