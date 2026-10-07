#!/usr/bin/env python3
"""Ejercicio 6 (partes A y B): cliente TCP que manda tres "mensajes".

Sirve para comprobar que TCP es un flujo de bytes: del otro lado no se
distinguen los tres send().

Uso:
    python3 ej6_cliente_tcp.py [puerto] [--pausa SEG]

    Servidor (otra terminal):  nc -l 8080 | od -c
                         o:    python3 ej6_servidor_tcp.py
"""
import argparse
import socket
import time

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Cliente TCP de 3 envíos")
    parser.add_argument("puerto", nargs="?", type=int, default=8080)
    parser.add_argument("--host", default="localhost")
    parser.add_argument("--pausa", type=float, default=0.0,
                        help="segundos entre envíos (parte A.2)")
    args = parser.parse_args()

    s = socket.create_connection((args.host, args.puerto))
    for msg in [b'HOLA', b'COMO', b'ESTAS']:
        s.send(msg)
        print(f"send({msg!r})")
        if args.pausa:
            time.sleep(args.pausa)
    s.close()
