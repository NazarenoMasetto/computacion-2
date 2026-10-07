#!/usr/bin/env python3
"""Adicional: servidor de threads con tope de clientes simultáneos.

Pasado el límite responde "servidor ocupado" y cierra, en vez de atender.

Uso:
    python3 ad_limite_conexiones.py [--port 8080] [--max 5] [--lento SEG]
"""
import argparse
import socket
import threading
import time


def atender(conn, cupo, lento):
    try:
        if lento:
            time.sleep(lento)
        with conn:
            while (datos := conn.recv(4096)):
                conn.sendall(datos)
    except (ConnectionResetError, BrokenPipeError):
        pass
    finally:
        cupo.release()          # libera el lugar al terminar


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--port', type=int, default=8080)
    ap.add_argument('--max', type=int, default=5)
    ap.add_argument('--lento', type=float, default=0.0)
    args = ap.parse_args()

    # semáforo acotado: cuenta los lugares libres (clase 11)
    cupo = threading.BoundedSemaphore(args.max)
    rechazados = 0
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as srv:
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind(('0.0.0.0', args.port))
        srv.listen(128)
        print(f'[limite] puerto {args.port} máximo {args.max} simultáneos', flush=True)
        while True:
            conn, direc = srv.accept()
            if cupo.acquire(blocking=False):
                threading.Thread(target=atender, args=(conn, cupo, args.lento),
                                 daemon=True).start()
            else:
                rechazados += 1
                try:
                    conn.sendall(b'ERROR servidor ocupado, intente mas tarde\n')
                except OSError:
                    pass
                conn.close()
                print(f'rechazado {direc} (total rechazados: {rechazados})', flush=True)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('\nServidor detenido')
