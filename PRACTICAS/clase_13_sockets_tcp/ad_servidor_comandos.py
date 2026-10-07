#!/usr/bin/env python3
"""Adicional: servidor de comandos por líneas (estilo SMTP en miniatura).

Comandos: TIME, ECHO <texto>, QUIT.

Uso:
    python3 ad_servidor_comandos.py [--port 8080]
    nc localhost 8080
"""
import argparse
import socket
import time

from ej3_framing_lineas import recibir_lineas


def procesar(linea: str):
    """Devuelve (respuesta, seguir_conectado)."""
    comando, _, resto = linea.strip().partition(' ')
    comando = comando.upper()
    if comando == 'TIME':
        return '200 ' + time.strftime('%Y-%m-%d %H:%M:%S'), True
    if comando == 'ECHO':
        return '200 ' + resto, True
    if comando == 'QUIT':
        return '221 chau', False
    return f'500 comando desconocido: {comando}', True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--port', type=int, default=8080)
    args = ap.parse_args()
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as srv:
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind(('0.0.0.0', args.port))
        srv.listen(5)
        print(f'[comandos] escuchando en {args.port}', flush=True)
        while True:
            conn, direc = srv.accept()
            try:
                with conn:
                    conn.sendall(b'220 listo (TIME, ECHO <txt>, QUIT)\n')
                    for linea in recibir_lineas(conn):
                        texto = linea.decode('utf-8', errors='replace').rstrip('\r')
                        resp, seguir = procesar(texto)
                        conn.sendall(resp.encode() + b'\n')
                        if not seguir:
                            break
            except (ConnectionResetError, BrokenPipeError):
                pass
            print(f'{direc} desconectado', flush=True)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('\nServidor detenido')
