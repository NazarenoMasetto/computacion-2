#!/usr/bin/env python3
"""Ej 4: qué hace connect() en un socket UDP.

Uso:
    python3 ej4_connect_udp.py [--port 9999]

Hace tres pruebas:
  1. connect() + send() a un puerto vacío -> ConnectionRefusedError
  2. sendto()/recvfrom() sin connect()    -> timeout
  3. socket conectado a A recibe un datagrama de B -> el kernel lo filtra
"""
import argparse
import socket


def prueba_con_connect(puerto):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(2)
    s.connect(('localhost', puerto))     # puerto donde no hay nadie
    s.send(b'hola')
    try:
        s.recv(4096)
        resultado = 'llegó algo (?)'
    except ConnectionRefusedError:
        resultado = 'ConnectionRefusedError'
    except TimeoutError:
        resultado = 'timeout'
    s.close()
    print(f'1. con connect():   {resultado}')


def prueba_sin_connect(puerto):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(2)
    s.sendto(b'hola', ('localhost', puerto))
    try:
        s.recvfrom(4096)
        resultado = 'llegó algo (?)'
    except ConnectionRefusedError:
        resultado = 'ConnectionRefusedError'
    except TimeoutError:
        resultado = 'timeout (2 s)'
    s.close()
    print(f'2. sin connect():   {resultado}')


def prueba_filtro(puerto):
    """El socket se 'conecta' a A; después B y A le mandan algo."""
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as yo, \
         socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as a, \
         socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as b:
        yo.bind(('localhost', 0))
        a.bind(('localhost', puerto + 1))
        b.bind(('localhost', puerto + 2))
        yo.connect(a.getsockname())
        yo.settimeout(1)
        b.sendto(b'soy B (intruso)', yo.getsockname())
        a.sendto(b'soy A (el conectado)', yo.getsockname())
        recibidos = []
        try:
            while True:
                recibidos.append(yo.recv(4096))
        except TimeoutError:
            pass
        print(f'3. conectado a A, recibí: {recibidos}  (lo de B lo descartó el kernel)')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--port', type=int, default=9999)
    args = ap.parse_args()
    prueba_con_connect(args.port)
    prueba_sin_connect(args.port)
    prueba_filtro(args.port)


if __name__ == '__main__':
    main()
