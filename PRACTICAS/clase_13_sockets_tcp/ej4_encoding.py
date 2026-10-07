#!/usr/bin/env python3
"""Ej 4: bytes vs str y el bug del carácter UTF-8 partido.

Uso:
    python3 ej4_encoding.py
"""
import codecs
import socket


def main():
    # 1. sendall() con str en vez de bytes
    a, b = socket.socketpair()
    try:
        a.sendall('hola')
    except TypeError as e:
        print(f"1. sendall('hola') -> TypeError: {e}")
    a.close(); b.close()

    # 2. longitudes en caracteres vs bytes
    print(f"2. 'ñ'.encode()   = {'ñ'.encode('utf-8')!r}")
    print(f"   'año'.encode() = {'año'.encode('utf-8')!r}")
    print(f"   len('año')={len('año')}  len(bytes)={len('año'.encode('utf-8'))}")

    # 3. carácter partido a la mitad
    datos = 'año'.encode('utf-8')
    primera_mitad = datos[:2]
    try:
        print(primera_mitad.decode('utf-8'))
    except UnicodeDecodeError as e:
        print(f'3. decode de {primera_mitad!r} -> UnicodeDecodeError: {e}')

    # 4. una solución: decodificador incremental (guarda el byte suelto)
    dec = codecs.getincrementaldecoder('utf-8')()
    texto = dec.decode(datos[:2]) + dec.decode(datos[2:])
    print(f'4. con decodificador incremental: {texto!r}')

    # 5. errors='replace' muestra el reemplazo
    print(f"5. errors='replace': {primera_mitad.decode('utf-8', errors='replace')!r}")


if __name__ == '__main__':
    main()
