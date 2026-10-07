#!/usr/bin/env python3
"""Ej 3 parte A: 200 datagramas con pérdida simulada (versión propia de perdidas.py).

Uso:
    python3 ej3_perdidas.py [PROB] [--port 8099]
    python3 ej3_perdidas.py 0.3
"""
import argparse
import random
import socket
import threading


def sendto_con_perdidas(sock, datos, destino, prob):
    """Como sendto(), pero a veces no manda. Devuelve len(datos) igual: miente."""
    if random.random() < prob:
        return len(datos)
    return sock.sendto(datos, destino)


def receptor(puerto, recibidos, listo):
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.bind(('localhost', puerto))
        listo.set()
        s.settimeout(1.0)
        while True:
            try:
                datos, _ = s.recvfrom(65535)
            except TimeoutError:
                return
            recibidos.append(int(datos.split(b'#')[1]))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('prob', type=float, nargs='?', default=0.3)
    ap.add_argument('--port', type=int, default=8099)
    ap.add_argument('--total', type=int, default=200)
    args = ap.parse_args()

    recibidos, listo = [], threading.Event()
    hilo = threading.Thread(target=receptor, args=(args.port, recibidos, listo))
    hilo.start()
    listo.wait()
    errores = 0
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        for i in range(args.total):
            try:
                sendto_con_perdidas(s, b'dato#%d' % i, ('localhost', args.port), args.prob)
            except OSError:
                errores += 1
    hilo.join()

    perdidos = args.total - len(recibidos)
    print(f'Enviados: {args.total}  Recibidos: {len(recibidos)}  '
          f'Perdidos: {perdidos} ({perdidos / args.total:.0%})')
    print(f'Errores vistos por el emisor: {errores}')
    print(f'Primeros faltantes: {sorted(set(range(args.total)) - set(recibidos))[:12]}')
    desordenados = sum(1 for a, b in zip(recibidos, recibidos[1:]) if b < a)
    print(f'Saltos hacia atrás en el orden de llegada: {desordenados}')


if __name__ == '__main__':
    main()
