#!/usr/bin/env python3
"""Ejercicio 2.3: el límite FD_SETSIZE de select().

Abre 1100 sockets para que el último tenga un número de fd > 1023, y
vigila SOLO ese con select() y con poll().

Uso:
    python3 ej2_fdsetsize.py [cantidad]      (default 1100)
"""
import select
import socket
import sys


def main():
    cantidad = int(sys.argv[1]) if len(sys.argv) > 1 else 1100
    relleno = [socket.socket() for _ in range(cantidad)]
    alto = relleno[-1]
    print('fd:', alto.fileno())

    try:
        select.select([alto], [], [], 0)
        print('select(): OK')
    except (ValueError, OSError) as e:
        print(f'select(): {type(e).__name__}: {e}')

    p = select.poll()
    p.register(alto, select.POLLIN)
    print('poll():', p.poll(0) or 'OK, sin eventos')

    for s in relleno:
        s.close()


if __name__ == '__main__':
    main()
