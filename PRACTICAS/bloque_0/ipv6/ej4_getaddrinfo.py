#!/usr/bin/env python3
"""Ejercicio 4: getaddrinfo() en detalle.

Uso: python3 ej4_getaddrinfo.py [host]     (default: google.com)
"""
import socket
import sys


def mostrar(titulo, *args, **kwargs):
    print(f"\n== {titulo}")
    try:
        infos = socket.getaddrinfo(*args, **kwargs)
    except socket.gaierror as e:
        print(f"  socket.gaierror: {e}  (errno={e.errno})")
        return []
    for familia, tipo, proto, canon, direccion in infos:
        print(f"  {familia.name:<9} {tipo.name:<12} proto={proto} {direccion}")
    print(f"  -> {len(infos)} resultado(s)")
    return infos


def main():
    host = sys.argv[1] if len(sys.argv) > 1 else "google.com"

    # 1. Servicio por nombre: 'http' se traduce a 80 usando /etc/services
    mostrar(f"1. getaddrinfo('{host}', 'http', SOCK_STREAM)",
            host, "http", type=socket.SOCK_STREAM)
    print(f"  socket.getservbyname('http') = {socket.getservbyname('http')}")

    # 2. Algunos servicios conocidos de /etc/services
    print("\n== 2. Servicios de /etc/services")
    for servicio in ("ssh", "https", "domain", "smtp", "postgresql"):
        try:
            print(f"  {servicio:<11} -> {socket.getservbyname(servicio, 'tcp')}/tcp")
        except OSError:
            print(f"  {servicio:<11} -> (no está en /etc/services)")

    # 3. Filtrar por familia
    mostrar(f"3. Solo AF_INET6", host, 80, socket.AF_INET6, socket.SOCK_STREAM)
    mostrar(f"3b. Solo AF_INET", host, 80, socket.AF_INET, socket.SOCK_STREAM)

    # 4. Nombre que no existe
    mostrar("4. Nombre inexistente", "no-existe-este-host.invalid", 80)

    # 5. AF_UNSPEC explícito vs. no pasar familia
    a = mostrar("5a. Sin familia", host, 80, type=socket.SOCK_STREAM)
    b = mostrar("5b. AF_UNSPEC explícito", host, 80, socket.AF_UNSPEC, socket.SOCK_STREAM)
    # Comparamos familias y cantidades: las IPs concretas pueden variar entre
    # consultas porque el DNS rota las respuestas (round-robin).
    fam_a = sorted(i[0].name for i in a)
    fam_b = sorted(i[0].name for i in b)
    print(f"\n  ¿Mismas familias y cantidad? {fam_a == fam_b}  (AF_UNSPEC = "
          f"{int(socket.AF_UNSPEC)}, que es justamente el default del parámetro family)")


if __name__ == "__main__":
    main()
