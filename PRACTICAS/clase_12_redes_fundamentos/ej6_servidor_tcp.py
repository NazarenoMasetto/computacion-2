#!/usr/bin/env python3
"""Ejercicio 6: servidor TCP que muestra cada recv() por separado.

Equivalente a `nc -l 8080 | od -c`, pero deja ver cuántas lecturas hizo
el servidor y qué bytes trajo cada una. La pausa antes de leer deja que
los tres envíos se acumulen en el buffer del kernel (como pasa cuando el
servidor está ocupado): ahí se ve que llegan pegados.

Uso:
    python3 ej6_servidor_tcp.py [puerto] [--espera SEG]
"""
import argparse
import socket
import time

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Servidor TCP que muestra cada recv()")
    parser.add_argument("puerto", nargs="?", type=int, default=8080)
    parser.add_argument("--espera", type=float, default=0.5,
                        help="segundos a esperar antes del primer recv (default 0.5)")
    args = parser.parse_args()

    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(("localhost", args.puerto))
    srv.listen(1)
    print(f"Escuchando en localhost:{args.puerto} ...")

    conn, origen = srv.accept()
    print(f"Conexión de {origen}")
    time.sleep(args.espera)          # simula un servidor que tarda en leer
    n = 0
    with conn:
        while True:
            datos = conn.recv(4096)
            if not datos:            # b'' = el cliente cerró (llegó el FIN)
                break
            n += 1
            print(f"recv #{n}: {datos!r} ({len(datos)} bytes)")
    print(f"Total: {n} recv() para 3 send() del cliente")
    srv.close()
