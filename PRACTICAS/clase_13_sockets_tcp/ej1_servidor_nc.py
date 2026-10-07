#!/usr/bin/env python3
"""Ej 1.2 / 1.3: servidor TCP mínimo para probar con `nc localhost 8080`.

Uso:
    python3 ej1_servidor_nc.py [--port 8080] [--sin-reuse] [--loop]

--sin-reuse  no setea SO_REUSEADDR (punto 6: ver "Address already in use")
--loop       sigue atendiendo clientes en vez de terminar (punto 5)
"""
import argparse
import socket


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--port', type=int, default=8080)
    ap.add_argument('--sin-reuse', action='store_true')
    ap.add_argument('--loop', action='store_true')
    args = ap.parse_args()

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as srv:
        if not args.sin_reuse:
            srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind(('0.0.0.0', args.port))
        srv.listen(5)
        print(f'Escuchando en 0.0.0.0:{args.port}...', flush=True)
        while True:
            conn, direc = srv.accept()
            with conn:
                # direc = (ip_cliente, puerto_efimero_cliente)
                print(f'Conexión desde {direc}', flush=True)
                datos = conn.recv(4096)
                conn.sendall(b'ECHO: ' + datos)
            if not args.loop:
                break   # la versión original atiende uno solo y termina


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('\nServidor detenido')
