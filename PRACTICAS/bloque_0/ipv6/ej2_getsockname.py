#!/usr/bin/env python3
"""Ejercicio 2 (puntos 7 y 8): la tupla de getsockname() en IPv4 vs IPv6.

Muestra el error de hacer 'host, puerto = sock.getsockname()' con IPv6
y la forma de escribirlo para que funcione con las dos familias.
"""
import socket


def probar(familia, direccion):
    nombre = "IPv6" if familia == socket.AF_INET6 else "IPv4"
    try:
        s = socket.socket(familia, socket.SOCK_STREAM)
    except OSError as e:
        print(f"[{nombre}] no se pudo crear el socket: {e}")
        print("        (el kernel de esta máquina no tiene IPv6 habilitado)")
        return
    with s:
        s.bind((direccion, 0))
        tupla = s.getsockname()
        print(f"[{nombre}] getsockname() = {tupla}  ({len(tupla)} elementos)")

        # Forma INCORRECTA: solo anda con IPv4
        try:
            host, puerto = s.getsockname()
            print(f"        host, puerto = ...  -> anda: {host} {puerto}")
        except ValueError as e:
            print(f"        host, puerto = ...  -> ValueError: {e}")

        # Forma CORRECTA: tomar los dos primeros elementos siempre
        host, puerto = s.getsockname()[:2]
        print(f"        getsockname()[:2]   -> {host} {puerto}")


if __name__ == "__main__":
    probar(socket.AF_INET, "127.0.0.1")
    probar(socket.AF_INET6, "::1")
