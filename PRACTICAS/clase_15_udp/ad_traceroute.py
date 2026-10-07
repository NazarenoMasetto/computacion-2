#!/usr/bin/env python3
"""Adicional: traceroute casero (UDP con TTL creciente + socket raw ICMP).

Necesita privilegios (root o CAP_NET_RAW) para el socket raw.

Uso:
    sudo python3 ad_traceroute.py DESTINO [--max-saltos 30] [--port 33434]
"""
import argparse
import socket
import time


def traceroute(destino, max_saltos, puerto, timeout):
    ip_destino = socket.gethostbyname(destino)
    print(f'traceroute a {destino} ({ip_destino}), máx {max_saltos} saltos')
    for ttl in range(1, max_saltos + 1):
        # raw ICMP para escuchar "time exceeded" (tipo 11) y "port unreachable" (3/3)
        with socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP) as rx, \
             socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as tx:
            rx.settimeout(timeout)
            tx.setsockopt(socket.IPPROTO_IP, socket.IP_TTL, ttl)
            inicio = time.perf_counter()
            tx.sendto(b'compu2', (ip_destino, puerto + ttl))   # puerto alto, nadie escucha
            salto, tipo = None, None
            limite = inicio + timeout
            while time.perf_counter() < limite:
                try:
                    paquete, (ip, _) = rx.recvfrom(1024)
                except TimeoutError:
                    break
                ihl = (paquete[0] & 0x0F) * 4          # largo de la cabecera IP
                icmp_tipo, icmp_codigo = paquete[ihl], paquete[ihl + 1]
                if icmp_tipo == 11 or (icmp_tipo == 3 and icmp_codigo == 3):
                    salto, tipo = ip, icmp_tipo
                    break
            rtt = (time.perf_counter() - inicio) * 1000
        if salto is None:
            print(f'{ttl:2d}  *')
            continue
        print(f'{ttl:2d}  {salto}  {rtt:.2f} ms')
        if tipo == 3:          # port unreachable: llegamos al destino
            break


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('destino')
    ap.add_argument('--max-saltos', type=int, default=30)
    ap.add_argument('--port', type=int, default=33434)
    ap.add_argument('--timeout', type=float, default=1.0)
    args = ap.parse_args()
    try:
        traceroute(args.destino, args.max_saltos, args.port, args.timeout)
    except PermissionError:
        print('Hace falta root (o CAP_NET_RAW) para abrir el socket raw ICMP.')


if __name__ == '__main__':
    main()
