#!/usr/bin/env python3
"""Ejercicio 7: observar los puertos efímeros que asigna el kernel.

Abre varias conexiones a la vez hacia el mismo destino e imprime el
socket local (getsockname) de cada una.

Uso:
    python3 ej7_puertos_efimeros.py                         # example.com:80 (consigna)
    python3 ej7_puertos_efimeros.py --host localhost --puerto 27081
    python3 ej7_puertos_efimeros.py --familia 4             # forzar IPv4 (tupla de 2)
    python3 ej7_puertos_efimeros.py --familia 6             # forzar IPv6 (tupla de 4)
    python3 ej7_puertos_efimeros.py --no-esperar            # no pide Enter (para tests)
"""
import argparse
import socket


def rango_efimero():
    """Lee el rango de puertos efímeros de Linux."""
    try:
        with open("/proc/sys/net/ipv4/ip_local_port_range") as f:
            bajo, alto = map(int, f.read().split())
            return bajo, alto
    except OSError:
        return None


def conectar(host, puerto, familia):
    """create_connection respeta lo que resuelva DNS; si se pide familia, se fuerza."""
    if familia is None:
        return socket.create_connection((host, puerto), timeout=5)
    fam = socket.AF_INET if familia == 4 else socket.AF_INET6
    info = socket.getaddrinfo(host, puerto, fam, socket.SOCK_STREAM)[0]
    s = socket.socket(info[0], info[1], info[2])
    s.settimeout(5)
    s.connect(info[4])
    return s


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Puertos efímeros")
    p.add_argument("--host", default="example.com")
    p.add_argument("--puerto", type=int, default=80)
    p.add_argument("-n", type=int, default=5, help="cantidad de conexiones")
    p.add_argument("--familia", type=int, choices=[4, 6])
    p.add_argument("--no-esperar", action="store_true")
    args = p.parse_args()

    rango = rango_efimero()
    if rango:
        print(f"Rango efímero de Linux: {rango[0]}-{rango[1]} "
              f"({rango[1] - rango[0] + 1} puertos)  | IANA: 49152-65535")

    try:
        conns = [conectar(args.host, args.puerto, args.familia) for _ in range(args.n)]
    except OSError as e:
        # Ej: forzar IPv6 contra un host o una máquina sin IPv6
        raise SystemExit(f"No se pudo conectar a {args.host}:{args.puerto} "
                         f"(familia={args.familia or 'auto'}): {e}")
    for c in conns:
        local = c.getsockname()
        remoto = c.getpeername()
        dentro = rango and rango[0] <= local[1] <= rango[1]
        print(f"local={local}  remoto={remoto}  "
              f"(tupla de {len(local)}, {'dentro' if dentro else 'FUERA'} del rango)")

    if not args.no_esperar:
        input("Enter para cerrar... (mientras tanto: ss -tn state established)")
    for c in conns:
        c.close()
