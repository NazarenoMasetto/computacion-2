#!/usr/bin/env python3
"""Ejercicio 4: servidor_select.py reescrito con selectors.

Desaparecen la lista `vigilados` y el diccionario de direcciones: el
selector lleva el registro, y el dato asociado (key.data) guarda la
dirección de cada cliente.

Uso:
    python3 ej4_servidor_selectors.py [--port 8080]
    python3 ej4_servidor_selectors.py --select-selector    # forzar select()
    python3 ej4_servidor_selectors.py --sin-unregister     # bug del 4.4
"""
import argparse
import selectors
import socket


def main():
    parser = argparse.ArgumentParser(description='Eco con selectors')
    parser.add_argument('--port', type=int, default=8080)
    parser.add_argument('--select-selector', action='store_true',
                        help='usar SelectSelector en vez del default')
    parser.add_argument('--sin-unregister', action='store_true',
                        help='cerrar sin unregister (bug a propósito)')
    args = parser.parse_args()

    sel = selectors.SelectSelector() if args.select_selector else selectors.DefaultSelector()

    servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    servidor.bind(('0.0.0.0', args.port))
    servidor.listen(128)
    servidor.setblocking(False)
    sel.register(servidor, selectors.EVENT_READ, None)   # data None = el que escucha
    print(f'Escuchando en :{args.port} con {type(sel).__name__}', flush=True)

    try:
        while True:
            for clave, _ in sel.select():
                if clave.data is None:
                    conn, direccion = servidor.accept()
                    conn.setblocking(False)
                    sel.register(conn, selectors.EVENT_READ, direccion)
                    print(f'+ cliente {direccion}  (fd {conn.fileno()})', flush=True)
                    continue

                conn = clave.fileobj
                try:
                    datos = conn.recv(4096)
                except ConnectionResetError:
                    datos = b''
                if datos:
                    conn.sendall(datos)        # eco simple, como el original
                else:
                    if not args.sin_unregister:
                        sel.unregister(conn)   # SIEMPRE antes de close()
                    conn.close()
                    print(f'- cliente {clave.data}', flush=True)
    except KeyboardInterrupt:
        print('\nServidor detenido')
    finally:
        sel.close()
        servidor.close()


if __name__ == '__main__':
    main()
