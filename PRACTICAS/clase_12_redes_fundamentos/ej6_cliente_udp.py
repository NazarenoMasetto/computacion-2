#!/usr/bin/env python3
"""Ejercicio 6 parte C: cliente UDP que manda tres datagramas.

Uso:
    python3 ej6_cliente_udp.py [puerto]     # default 8080
"""
import socket
import sys

if __name__ == "__main__":
    puerto = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    for msg in [b'HOLA', b'COMO', b'ESTAS']:
        s.sendto(msg, ('localhost', puerto))
        print(f"sendto({msg!r})")
    s.close()
