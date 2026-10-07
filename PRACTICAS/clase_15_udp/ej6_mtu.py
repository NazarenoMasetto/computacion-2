#!/usr/bin/env python3
"""Ej 6: MTU, fragmentación y por qué fragmentar multiplica las pérdidas.

Uso:
    python3 ej6_mtu.py [--port 8083] [--mtu 1500] [--perdida 0.05] [--veces 20]

1. Muestra el MTU de cada interfaz (igual que `ip link show | grep mtu`).
2. Manda datagramas de 60000 y de 1000 bytes a un receptor local.
   - Con --perdida 0 confía en la red real (por ej. con `tc netem loss 5%` activo).
   - Con --perdida P SIMULA la pérdida por FRAGMENTO: el datagrama llega
     solo si llegan todos sus fragmentos (que es lo que hace IP de verdad).
"""
import argparse
import math
import os
import random
import socket
import threading
import time


def mostrar_mtus():
    base = '/sys/class/net'
    for iface in sorted(os.listdir(base)):
        try:
            with open(f'{base}/{iface}/mtu') as f:
                print(f'  {iface}: mtu {f.read().strip()}')
        except OSError:
            pass


def fragmentos(tam_payload, mtu):
    """Cantidad de fragmentos IP para un datagrama UDP de tam_payload bytes."""
    por_fragmento = (mtu - 20) // 8 * 8         # datos por fragmento (múltiplo de 8)
    return math.ceil((tam_payload + 8) / por_fragmento)   # +8 de cabecera UDP


def receptor(sock, contador, fin):
    sock.settimeout(0.2)
    while True:
        try:
            datos, _ = sock.recvfrom(65535)
            contador[len(datos)] = contador.get(len(datos), 0) + 1
        except TimeoutError:
            if fin.is_set():
                return      # ya no se manda nada y el buffer quedó vacío


def probar(tam, args, puerto):
    rx = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    rx.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 4 * 1024 * 1024)
    rx.bind(('localhost', puerto))
    contador, fin = {}, threading.Event()
    hilo = threading.Thread(target=receptor, args=(rx, contador, fin))
    hilo.start()

    k = fragmentos(tam, args.mtu)
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as tx:
        for _ in range(args.veces):
            # simulación: se pierde si se pierde CUALQUIERA de sus k fragmentos
            perdido = any(random.random() < args.perdida for _ in range(k))
            if not perdido:
                tx.sendto(b'x' * tam, ('localhost', puerto))
            time.sleep(0.002)   # no desbordar el buffer del receptor
    fin.set()
    hilo.join()
    rx.close()
    llegaron = contador.get(tam, 0)
    teorico = (1 - args.perdida) ** k
    print(f'  {tam:>6} bytes = {k:>2} fragmento(s): llegaron {llegaron}/{args.veces} '
          f'({llegaron / args.veces:.0%}); teórico (1-p)^k = {teorico:.0%}')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--port', type=int, default=8083)
    ap.add_argument('--mtu', type=int, default=1500, help='MTU a suponer (Ethernet)')
    ap.add_argument('--perdida', type=float, default=0.05)
    ap.add_argument('--veces', type=int, default=20)
    args = ap.parse_args()

    print('MTU de las interfaces:')
    mostrar_mtus()
    print(f'Payload UDP sin fragmentar con MTU {args.mtu}: '
          f'{args.mtu} - 20 (IP) - 8 (UDP) = {args.mtu - 28} bytes')
    print(f'Pérdida por fragmento: {args.perdida:.0%}, {args.veces} envíos de cada tamaño')
    for tam in (60000, 1000):
        probar(tam, args, args.port)


if __name__ == '__main__':
    main()
