#!/usr/bin/env python3
"""Ej 2.2: un recvfrom() con buffer chico TRUNCA el datagrama.

Uso:
    python3 ej2_truncado.py [--port 8081]
"""
import argparse
import socket


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--port', type=int, default=8081)
    args = ap.parse_args()

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as r, \
         socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        r.bind(('localhost', args.port))
        s.sendto(b'X' * 100, ('localhost', args.port))

        datos, _ = r.recvfrom(10)          # buffer de 10 para un datagrama de 100
        print(f'primer recvfrom: {len(datos)} bytes')

        r.settimeout(1.0)
        try:
            datos2, _ = r.recvfrom(65535)
            print(f'segundo recvfrom: {len(datos2)} bytes')
        except TimeoutError:
            print('segundo recvfrom: nada (los 90 bytes se descartaron)')

        # con recvmsg() el kernel avisa que truncó (flag MSG_TRUNC)
        s.sendto(b'Y' * 100, ('localhost', args.port))
        datos, _anc, flags, _ = r.recvmsg(10)
        print(f'recvmsg(10): {len(datos)} bytes, MSG_TRUNC={bool(flags & socket.MSG_TRUNC)}')


if __name__ == '__main__':
    main()
