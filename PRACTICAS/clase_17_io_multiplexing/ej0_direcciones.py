#!/usr/bin/env python3
"""Ejercicio 0: direcciones en el código (misma red, tupla IPv6,
getaddrinfo y dual-stack).

Corre las cuatro partes en orden. Si la máquina no tiene IPv6 (pasa en
algunos contenedores) lo informa y sigue con lo que se pueda.

Uso:
    python3 ej0_direcciones.py [--port 8080] [--v6only] [--host google.com]
"""
import argparse
import ipaddress
import socket


def parte_1():
    print('=== 0.1 Misma red o no ===')
    red = ipaddress.ip_network('192.168.1.0/24')
    for ip in ('192.168.1.37', '192.168.2.10'):
        dentro = ipaddress.ip_address(ip) in red
        destino = 'entrega directa (ARP en la LAN)' if dentro else 'al gateway'
        print(f'  {ip} in {red}: {dentro} -> {destino}')


def host_puerto(direccion):
    """Forma portable: sirve para tuplas de 2 (IPv4) y de 4 (IPv6)."""
    return direccion[0], direccion[1]


def parte_2():
    print('\n=== 0.2 La tupla de IPv6 ===')
    try:
        s = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
    except OSError as e:
        print(f'  Sin IPv6 en esta máquina: {e}')
        return
    with s:
        s.bind(('::1', 0))
        direccion = s.getsockname()
        print(f'  getsockname() = {direccion}  ({len(direccion)} elementos)')
        try:
            host, puerto = direccion            # falla con 4 elementos
        except ValueError as e:
            print(f'  host, puerto = ... -> ValueError: {e}')
        print(f'  forma portable: host, puerto = dir[0], dir[1] -> {host_puerto(direccion)}')


def parte_3(host):
    print(f'\n=== 0.3 getaddrinfo({host!r}, 80) ===')
    try:
        infos = socket.getaddrinfo(host, 80, type=socket.SOCK_STREAM)
    except socket.gaierror as e:
        print(f'  no se pudo resolver: {e}')
        return
    for info in infos:
        print(f'  {info[0].name:8} {info[4]}')
    # Lo que hace create_connection: probar en orden hasta que una conecte
    for familia, tipo, proto, _, direccion in infos:
        try:
            with socket.socket(familia, tipo, proto) as s:
                s.settimeout(2)
                s.connect(direccion)
                print(f'  conectó con {familia.name} {direccion}')
                break
        except OSError as e:
            print(f'  falló {familia.name} {direccion}: {e}')


def parte_4(puerto, v6only):
    print(f'\n=== 0.4 Dual-stack (IPV6_V6ONLY={int(v6only)}) en :{puerto} ===')
    try:
        srv = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
    except OSError as e:
        print(f'  Sin IPv6 en esta máquina: {e}')
        return
    with srv:
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # Explícito: el default depende de /proc/sys/net/ipv6/bindv6only
        srv.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, int(v6only))
        srv.bind(('::', puerto))
        srv.listen(5)
        srv.settimeout(2)
        for familia, ip in ((socket.AF_INET6, '::1'), (socket.AF_INET, '127.0.0.1')):
            try:
                with socket.socket(familia, socket.SOCK_STREAM) as cli:
                    cli.settimeout(2)
                    cli.connect((ip, puerto))
                    conn, direccion = srv.accept()
                    conn.close()
                    print(f'  cliente {ip:>9} -> el servidor ve {direccion[0]}')
            except OSError as e:
                print(f'  cliente {ip:>9} -> no pudo conectar: {e}')


def main():
    parser = argparse.ArgumentParser(description='Ejercicio 0 de la clase 17')
    parser.add_argument('--port', type=int, default=8080)
    parser.add_argument('--v6only', action='store_true')
    parser.add_argument('--host', default='google.com')
    args = parser.parse_args()

    parte_1()
    parte_2()
    parte_3(args.host)
    parte_4(args.port, args.v6only)


if __name__ == '__main__':
    main()
