#!/usr/bin/env python3
"""Adicional: servidor de tiempo estilo RFC 868 sobre UDP.

El servidor responde a cualquier datagrama con 4 bytes: segundos, empaquetados
con struct.pack('!I'). La RFC 868 cuenta desde 1900 (no desde 1970), así que
se suma la diferencia: 2208988800 s. Con --epoch-unix se usa 1970 tal cual.

Uso:
    python3 ad_tiempo.py servidor [--port 8037] [--atraso SEG]
    python3 ad_tiempo.py cliente  [--port 8037]
"""
import argparse
import socket
import struct
import time

DESDE_1900 = 2_208_988_800     # segundos entre 1900-01-01 y 1970-01-01


def servidor(puerto, atraso):
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(('0.0.0.0', puerto))
        print(f'[tiempo] puerto {puerto} (atraso simulado {atraso}s)', flush=True)
        while True:
            _, origen = s.recvfrom(1024)
            ahora = int(time.time() + atraso) + DESDE_1900
            s.sendto(struct.pack('!I', ahora & 0xFFFFFFFF), origen)


def cliente(puerto):
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.settimeout(2.0)
        t0 = time.time()
        s.sendto(b'', ('localhost', puerto))
        datos, _ = s.recvfrom(1024)
        t1 = time.time()
    (seg,) = struct.unpack('!I', datos)
    remoto = seg - DESDE_1900
    local = (t0 + t1) / 2          # suponemos ida y vuelta simétricas
    print(f'Hora del servidor: {time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(remoto))}')
    print(f'Hora local:        {time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(local))}')
    print(f'RTT: {(t1 - t0) * 1000:.2f} ms   desfasaje servidor-local: {remoto - local:+.1f} s '
          f'(resolución de 1 s)')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('rol', choices=['servidor', 'cliente'])
    ap.add_argument('--port', type=int, default=8037)
    ap.add_argument('--atraso', type=float, default=0.0, help='desfasaje simulado del servidor')
    args = ap.parse_args()
    if args.rol == 'servidor':
        servidor(args.port, args.atraso)
    else:
        cliente(args.port)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('\nCortado')
