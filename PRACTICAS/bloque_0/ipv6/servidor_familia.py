#!/usr/bin/env python3
"""Adicional: servidor que le dice al cliente por qué familia llegó y cómo lo ve.

Si puede, usa un socket dual-stack; si el kernel no tiene IPv6, cae a IPv4
(así sigue sirviendo para diagnosticar). Se prueba con nc o con ej3_cliente.py.

Uso: python3 servidor_familia.py [--port 8080] [--max N]
"""
import argparse
import ipaddress
import socket


def crear_servidor(puerto):
    """Intenta dual-stack; si no hay IPv6 en el sistema usa IPv4."""
    try:
        s = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 0)
        s.bind(("::", puerto))
        modo = "dual-stack"
    except OSError:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(("0.0.0.0", puerto))
        modo = "solo IPv4 (el sistema no tiene IPv6)"
    s.listen(5)
    return s, modo


def describir(peer, local):
    """Arma el texto de diagnóstico para el cliente."""
    host = peer[0]
    ip = ipaddress.ip_address(host.split("%")[0])
    if ip.version == 6 and ip.ipv4_mapped:
        familia = f"IPv4 (llegó mapeada como {host} a un socket IPv6)"
        host = str(ip.ipv4_mapped)
    else:
        familia = f"IPv{ip.version}"
    lineas = [
        f"Llegaste por: {familia}",
        f"Te veo como:  {host} puerto {peer[1]}",
        f"Me hablaste a: {local[0]} puerto {local[1]}",
    ]
    if len(peer) == 4:
        lineas.append(f"flowinfo={peer[2]} scope_id={peer[3]}")
    return "\n".join(lineas) + "\n"


def main():
    parser = argparse.ArgumentParser(description="Servidor que reporta la familia del cliente.")
    parser.add_argument("-p", "--port", type=int, default=8080, help="Puerto (default: 8080)")
    parser.add_argument("--max", type=int, default=0, help="Terminar tras N conexiones")
    args = parser.parse_args()

    servidor, modo = crear_servidor(args.port)
    print(f"Escuchando en el puerto {args.port} — {modo}", flush=True)
    atendidos = 0
    with servidor:
        try:
            while not args.max or atendidos < args.max:
                conn, peer = servidor.accept()
                with conn:
                    texto = describir(peer, conn.getsockname())
                    print(texto.replace("\n", " | "), flush=True)
                    conn.sendall(texto.encode())
                atendidos += 1
        except KeyboardInterrupt:
            print("\nServidor detenido")


if __name__ == "__main__":
    main()
