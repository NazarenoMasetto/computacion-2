#!/usr/bin/env python3
"""Ej 1 y 2.1: servidor y cliente eco UDP (versión propia).

Uso:
    python3 ej1_echo_udp.py servidor [--port 8080]
    python3 ej1_echo_udp.py cliente  [--port 8080] [--mensaje TEXTO] [--sin-timeout]
    python3 ej1_echo_udp.py tres     [--port 8080]
"""
import argparse
import socket


def servidor(puerto):
    """Un solo socket para todos los clientes: no hay listen() ni accept()."""
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(('0.0.0.0', puerto))
        print(f'Escuchando UDP en 0.0.0.0:{puerto}', flush=True)
        n = 0
        while True:
            datos, origen = s.recvfrom(65535)    # datos + (ip, puerto) del remitente
            n += 1
            print(f'  [{n}] recvfrom {len(datos)} bytes de {origen[0]}:{origen[1]}: '
                  f'{datos[:60]!r}', flush=True)
            s.sendto(datos, origen)              # contestar a quien mandó


def cliente(puerto, mensaje, con_timeout):
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        if con_timeout:
            s.settimeout(2.0)   # sin esto, si nadie contesta esperamos para siempre
        s.sendto(mensaje, ('localhost', puerto))
        print(f'puerto efímero asignado: {s.getsockname()[1]}', flush=True)
        try:
            respuesta, origen = s.recvfrom(65535)
            print(f'eco de {origen}: {respuesta!r}')
        except TimeoutError:
            print('Sin respuesta en 2s. ¿Está corriendo el servidor?')
        except ConnectionRefusedError:
            # en loopback a veces el ICMP "port unreachable" llega como error
            print('ConnectionRefusedError (llegó un ICMP port unreachable)')


def tres(puerto):
    """Tres sendto() -> el servidor ve tres recvfrom()."""
    enviados = [b'HOLA', b'COMO', b'ESTAS']
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.settimeout(2.0)
        for msg in enviados:
            s.sendto(msg, ('localhost', puerto))
        recibidos = []
        try:
            for _ in enviados:
                recibidos.append(s.recvfrom(65535)[0])
        except TimeoutError:
            pass
    print(f'enviados:  {enviados}')
    print(f'recibidos: {recibidos}')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('modo', choices=['servidor', 'cliente', 'tres'])
    ap.add_argument('--port', type=int, default=8080)
    ap.add_argument('--mensaje', default='hola mundo')
    ap.add_argument('--sin-timeout', action='store_true')
    args = ap.parse_args()
    if args.modo == 'servidor':
        servidor(args.port)
    elif args.modo == 'tres':
        tres(args.port)
    else:
        cliente(args.port, args.mensaje.encode(), not args.sin_timeout)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('\nCortado')
