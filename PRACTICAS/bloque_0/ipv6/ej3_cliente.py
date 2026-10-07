#!/usr/bin/env python3
"""Ejercicio 3 Parte E: cliente agnóstico de familia con getaddrinfo().

Prueba TODAS las direcciones que devuelve getaddrinfo() en orden, hasta
que una conecte. Sirve también para las Partes A-C pasándole 127.0.0.1 o ::1.

Uso:
  python3 ej3_cliente.py [host] [--port 8080]
"""
import argparse
import socket
import sys


def conectar(host, puerto, timeout=5):
    """Devuelve un socket conectado o lanza OSError si ninguna dirección anduvo."""
    ultimo_error = None
    for familia, tipo, proto, _, direccion in socket.getaddrinfo(
            host, puerto, type=socket.SOCK_STREAM):
        nombre = "IPv6" if familia == socket.AF_INET6 else "IPv4"
        print(f"  probando {nombre} {direccion[0]} ...", end=" ")
        try:
            s = socket.socket(familia, tipo, proto)
        except OSError as e:
            # Ej: el kernel no soporta AF_INET6
            print(f"no se pudo crear el socket ({e.strerror})")
            ultimo_error = e
            continue
        s.settimeout(timeout)
        try:
            s.connect(direccion)
        except OSError as e:
            print(f"falló ({e.strerror or e})")
            s.close()
            ultimo_error = e
            continue                    # seguimos con la próxima dirección
        print("conectado")
        return s
    raise ultimo_error or OSError(f"getaddrinfo no devolvió direcciones para {host}")


def main():
    parser = argparse.ArgumentParser(description="Cliente TCP agnóstico de familia.")
    parser.add_argument("host", nargs="?", default="localhost",
                        help="Host o IP (default: localhost)")
    parser.add_argument("-p", "--port", type=int, default=8080, help="Puerto (default: 8080)")
    args = parser.parse_args()

    try:
        s = conectar(args.host, args.port)
    except socket.gaierror as e:
        print(f"No se pudo resolver '{args.host}': {e}", file=sys.stderr)
        sys.exit(1)
    except OSError as e:
        print(f"Ninguna dirección funcionó: {e}", file=sys.stderr)
        sys.exit(1)
    with s:
        print(f"  respuesta: {s.recv(1024).decode().strip()}")


if __name__ == "__main__":
    main()
