#!/usr/bin/env python3
"""Ejercicio 6 parte C: receptor UDP, imprime cada datagrama que llega.

Muestra que UDP preserva los límites: cada sendto() del cliente produce
exactamente un recvfrom() acá.

Uso:
    python3 udp_srv.py [puerto]       # default 8080
"""
import socket
import sys

if __name__ == "__main__":
    HOST = 'localhost'
    PUERTO = int(sys.argv[1]) if len(sys.argv) > 1 else 8080

    # SOCK_DGRAM = UDP. No hay listen() ni accept(): no hay conexión que aceptar.
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind((HOST, PUERTO))
    s.settimeout(5)

    print(f"Esperando datagramas en {HOST}:{PUERTO} (5s de timeout)...")
    n = 0
    try:
        while True:
            datos, origen = s.recvfrom(4096)
            n += 1
            print(f"recv: {datos!r} de {origen}")
    except socket.timeout:
        print(f"(timeout, fin) -> {n} recvfrom() con datos")
    finally:
        s.close()
