#!/usr/bin/env python3
"""Ejercicio 3 (OBLIGATORIO): servidor TCP solo-IPv4, dual-stack o solo-IPv6.

Modos:
  v4      Parte A: AF_INET en 0.0.0.0 (un cliente ::1 no puede conectar)
  dual    Parte B: AF_INET6 en :: con IPV6_V6ONLY=0 (atiende las dos familias)
  v6only  Parte C: AF_INET6 en :: con IPV6_V6ONLY=1 (rechaza IPv4)

Uso:
  python3 ej3_servidor.py [--modo dual] [--port 8080] [--max N]
"""
import argparse
import ipaddress
import socket
import sys


def normalizar(host):
    """Parte D: ::ffff:1.2.3.4 -> 1.2.3.4; el resto queda igual."""
    try:
        direccion = ipaddress.ip_address(host.split("%")[0])
    except ValueError:
        return host
    if direccion.version == 6 and direccion.ipv4_mapped:
        return str(direccion.ipv4_mapped)
    return host


def crear_socket(modo, puerto):
    if modo == "v4":
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(("0.0.0.0", puerto))
    else:
        s = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # Parte B/C: SIEMPRE explícito, el default cambia según el sistema
        v6only = 1 if modo == "v6only" else 0
        s.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, v6only)
        s.bind(("::", puerto))
    s.listen(5)
    return s


def main():
    parser = argparse.ArgumentParser(description="Servidor TCP para probar dual-stack.")
    parser.add_argument("--modo", choices=["v4", "dual", "v6only"], default="dual",
                        help="Tipo de socket (default: dual)")
    parser.add_argument("-p", "--port", type=int, default=8080,
                        help="Puerto (default: 8080)")
    parser.add_argument("--max", type=int, default=0,
                        help="Terminar después de N conexiones (0 = infinito)")
    args = parser.parse_args()

    try:
        servidor = crear_socket(args.modo, args.port)
    except OSError as e:
        print(f"Error al crear el socket ({args.modo}): {e}", file=sys.stderr)
        if e.errno == 97:
            print("Esta máquina no tiene IPv6 en el kernel; probá con --modo v4",
                  file=sys.stderr)
        sys.exit(1)

    print(f"[{args.modo}] escuchando en {servidor.getsockname()[:2]}", flush=True)
    atendidos = 0
    with servidor:
        try:
            while not args.max or atendidos < args.max:
                conn, peer = servidor.accept()
                crudo = peer[0]                 # peer tiene 2 o 4 elementos
                limpio = normalizar(crudo)
                marca = "  <- IPv4 mapeada" if crudo != limpio else ""
                print(f"  conexión de {crudo} (normalizado: {limpio}){marca}", flush=True)
                with conn:
                    conn.sendall(f"hola {limpio}, te atiende el servidor {args.modo}\n".encode())
                atendidos += 1
        except KeyboardInterrupt:
            print("\nServidor detenido")


if __name__ == "__main__":
    main()
