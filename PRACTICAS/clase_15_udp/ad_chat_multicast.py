#!/usr/bin/env python3
"""Adicional: chat por multicast UDP. Lo que escribe uno lo ven todos.

Uso (en varias terminales):
    python3 ad_chat_multicast.py --nombre ana [--grupo 239.1.2.3] [--port 8084]
    escribir líneas; Ctrl+D o Ctrl+C para salir
"""
import argparse
import socket
import struct
import sys
import threading


def abrir_receptor(grupo, puerto):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)   # varios en la misma máquina
    s.bind(('', puerto))
    # unirse al grupo en todas las interfaces (IGMP join)
    mreq = struct.pack('4s4s', socket.inet_aton(grupo), socket.inet_aton('0.0.0.0'))
    s.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
    return s


def escuchar(sock):
    while True:
        datos, origen = sock.recvfrom(65535)
        print(f'\r{datos.decode(errors="replace")}', flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--nombre', default='anonimo')
    ap.add_argument('--grupo', default='239.1.2.3')    # rango administrativo/local
    ap.add_argument('--port', type=int, default=8084)
    ap.add_argument('--ttl', type=int, default=1, help='1 = no sale de la red local')
    args = ap.parse_args()

    rx = abrir_receptor(args.grupo, args.port)
    threading.Thread(target=escuchar, args=(rx,), daemon=True).start()

    tx = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    tx.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, args.ttl)
    tx.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_LOOP, 1)   # verme a mí también
    destino = (args.grupo, args.port)
    tx.sendto(f'* {args.nombre} entró al chat'.encode(), destino)
    try:
        for linea in sys.stdin:
            if linea.strip():
                # UN solo envío, sin importar cuántos estén escuchando
                tx.sendto(f'[{args.nombre}] {linea.rstrip()}'.encode(), destino)
    except KeyboardInterrupt:
        pass
    tx.sendto(f'* {args.nombre} salió'.encode(), destino)


if __name__ == '__main__':
    main()
