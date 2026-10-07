#!/usr/bin/env python3
"""Adicional: transferencia de archivos con framing por longitud.

Protocolo: [mensaje: nombre][mensaje: contenido en bloques...][mensaje vacío = fin]
Cada mensaje lleva prefijo de 4 bytes; así el archivo puede ser de cualquier
tamaño sin cargarlo entero en memoria.

Uso:
    python3 ad_transferencia.py servidor [--port 8080] [--destino recibidos/]
    python3 ad_transferencia.py cliente ARCHIVO [--port 8080]
    md5sum ARCHIVO recibidos/ARCHIVO
"""
import argparse
import hashlib
import os
import socket

from ej3_framing_longitud import enviar_mensaje, recibir_mensaje

BLOQUE = 64 * 1024


def servidor(puerto, destino):
    os.makedirs(destino, exist_ok=True)
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as srv:
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind(('0.0.0.0', puerto))
        srv.listen(5)
        print(f'[archivos] escuchando en {puerto}, guardo en {destino}', flush=True)
        while True:
            conn, direc = srv.accept()
            with conn:
                nombre = recibir_mensaje(conn)
                if not nombre:
                    continue
                # basename: que el cliente no pueda escribir fuera de destino
                ruta = os.path.join(destino, os.path.basename(nombre.decode()))
                md5 = hashlib.md5()
                total = 0
                with open(ruta, 'wb') as f:
                    while (bloque := recibir_mensaje(conn)):   # b'' o None = fin
                        f.write(bloque)
                        md5.update(bloque)
                        total += len(bloque)
                enviar_mensaje(conn, md5.hexdigest().encode())
                print(f'{direc}: {ruta} ({total} bytes) md5={md5.hexdigest()}', flush=True)


def cliente(puerto, archivo):
    md5 = hashlib.md5()
    with socket.create_connection(('localhost', puerto)) as s, open(archivo, 'rb') as f:
        enviar_mensaje(s, os.path.basename(archivo).encode())
        while (bloque := f.read(BLOQUE)):
            enviar_mensaje(s, bloque)
            md5.update(bloque)
        enviar_mensaje(s, b'')            # fin del archivo
        md5_remoto = recibir_mensaje(s).decode()
    print(f'md5 local:  {md5.hexdigest()}')
    print(f'md5 remoto: {md5_remoto}')
    print('OK, llegó íntegro' if md5_remoto == md5.hexdigest() else 'ERROR: difieren')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('rol', choices=['servidor', 'cliente'])
    ap.add_argument('archivo', nargs='?')
    ap.add_argument('--port', type=int, default=8080)
    ap.add_argument('--destino', default='recibidos')
    args = ap.parse_args()
    if args.rol == 'servidor':
        servidor(args.port, args.destino)
    else:
        cliente(args.port, args.archivo)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('\nCortado')
