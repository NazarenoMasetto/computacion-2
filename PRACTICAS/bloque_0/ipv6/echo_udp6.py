#!/usr/bin/env python3
"""Ejercicio 5: echo_udp.py de la clase 15 adaptado a IPv6 (AF_INET6 y ::1).

Lo único que cambia es la familia, la dirección, y que la tupla de origen
de recvfrom() ahora tiene 4 elementos (host, puerto, flowinfo, scope_id).

Uso:
    python3 echo_udp6.py servidor [puerto]
    python3 echo_udp6.py cliente  [puerto] [mensaje]
"""
import socket
import sys

PUERTO = 8080


def servidor(puerto):
    with socket.socket(socket.AF_INET6, socket.SOCK_DGRAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(("::1", puerto))
        print(f"Escuchando UDP en [::1]:{puerto} (Ctrl+C para salir)", flush=True)
        n = 0
        while True:
            datos, origen = s.recvfrom(65535)
            n += 1
            # origen = (host, puerto, flowinfo, scope_id): 4 elementos
            print(f"  [{n}] {len(datos)} bytes de [{origen[0]}]:{origen[1]} "
                  f"(tupla de {len(origen)} elementos: {origen})", flush=True)
            s.sendto(datos, origen)


def cliente(puerto, mensaje):
    with socket.socket(socket.AF_INET6, socket.SOCK_DGRAM) as s:
        s.settimeout(2.0)
        s.sendto(mensaje, ("::1", puerto))
        print(f"puerto efímero asignado: {s.getsockname()[1]}")
        try:
            respuesta, origen = s.recvfrom(65535)
            print(f"eco de {origen}: {respuesta!r}")
        except TimeoutError:
            print("Sin respuesta en 2s. ¿Está corriendo el servidor?")


if __name__ == "__main__":
    modo = sys.argv[1] if len(sys.argv) > 1 else "servidor"
    puerto = int(sys.argv[2]) if len(sys.argv) > 2 else PUERTO
    try:
        if modo == "servidor":
            servidor(puerto)
        else:
            msg = sys.argv[3].encode() if len(sys.argv) > 3 else b"hola mundo"
            cliente(puerto, msg)
    except KeyboardInterrupt:
        print("\nCortado")
    except OSError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
