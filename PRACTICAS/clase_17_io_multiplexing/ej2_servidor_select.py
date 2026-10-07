#!/usr/bin/env python3
"""Ejercicio 2: servidor eco con select(), con los bugs del 2.2 activables.

Es el servidor_select.py de la clase, más dos opciones para reproducir
lo que pasa si no se saca el socket cerrado de la lista vigilada:

    --bug            no hace vigilados.remove(sock) (pero sí close())
    --bug-sin-close  no hace remove NI close: el fd sigue abierto y en EOF

Uso:
    python3 ej2_servidor_select.py [--port 8080] [--bug | --bug-sin-close]
    nc localhost 8080        (en varias terminales)
"""
import argparse
import select
import socket


def main():
    parser = argparse.ArgumentParser(description='Eco con select()')
    parser.add_argument('--port', type=int, default=8080)
    parser.add_argument('--bug', action='store_true')
    parser.add_argument('--bug-sin-close', action='store_true')
    args = parser.parse_args()

    servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    servidor.bind(('0.0.0.0', args.port))
    servidor.listen(128)
    print(f'Escuchando en :{args.port} (un solo hilo)', flush=True)

    vigilados = [servidor]
    direcciones = {}
    vueltas = 0                       # cuántas veces volvió select()

    try:
        while True:
            listos, _, _ = select.select(vigilados, [], [])
            vueltas += 1
            if vueltas % 100_000 == 0:
                print(f'  select() ya volvió {vueltas} veces...', flush=True)

            for sock in listos:
                if sock is servidor:
                    conn, direccion = servidor.accept()
                    conn.setblocking(False)
                    vigilados.append(conn)
                    direcciones[conn] = direccion
                    print(f'+ cliente {direccion}  (total: {len(vigilados) - 1})',
                          flush=True)
                    continue

                datos = sock.recv(4096)
                if datos:
                    sock.sendall(datos)
                elif args.bug_sin_close:
                    # El fd sigue en EOF: select() lo reporta listo SIEMPRE
                    pass
                else:
                    # recv() vacío = el cliente cerró. Esta línea detecta el cierre.
                    if not args.bug:
                        vigilados.remove(sock)
                    d = direcciones.pop(sock, '?')
                    sock.close()
                    print(f'- cliente {d}  (total: {len(vigilados) - 1})', flush=True)
    except KeyboardInterrupt:
        print('\nServidor detenido')
    finally:
        for s in vigilados:
            s.close()


if __name__ == '__main__':
    main()
