#!/usr/bin/env python3
"""Las cuatro estrategias de servidor eco en un solo archivo (versión propia).

Uso:
    python3 servidores_eco.py --modo secuencial|threads|fork|pool
                              [--port 8080] [--lento SEG] [--workers N]
"""
import argparse
import os
import signal
import socket
import threading
import time
from concurrent.futures import ThreadPoolExecutor


def eco(conn, lento):
    """Atiende un cliente: espera `lento` y devuelve todo hasta que cierre."""
    if lento:
        time.sleep(lento)          # simula trabajo por cliente
    with conn:
        while (datos := conn.recv(4096)):
            conn.sendall(datos)


def eco_seguro(conn, lento):
    try:
        eco(conn, lento)
    except (ConnectionResetError, BrokenPipeError):
        pass


def cosechar(signum, frame):
    """Recoge TODOS los hijos terminados (las SIGCHLD no se encolan)."""
    while True:
        try:
            pid, _ = os.waitpid(-1, os.WNOHANG)
        except ChildProcessError:
            return
        if pid == 0:
            return


def servir(modo, srv, lento, workers):
    if modo == 'secuencial':
        while True:
            conn, _ = srv.accept()
            eco_seguro(conn, lento)
    elif modo == 'threads':
        while True:
            conn, _ = srv.accept()
            threading.Thread(target=eco_seguro, args=(conn, lento), daemon=True).start()
    elif modo == 'pool':
        with ThreadPoolExecutor(max_workers=workers) as pool:
            while True:
                conn, _ = srv.accept()
                pool.submit(eco_seguro, conn, lento)
    else:  # fork
        signal.signal(signal.SIGCHLD, cosechar)
        while True:
            try:
                conn, _ = srv.accept()
            except InterruptedError:
                continue
            if os.fork() == 0:
                srv.close()                # el hijo no necesita el socket que escucha
                eco_seguro(conn, lento)
                os._exit(0)
            conn.close()                   # el padre cierra su copia


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--modo', choices=['secuencial', 'threads', 'fork', 'pool'],
                    default='threads')
    ap.add_argument('--port', type=int, default=8080)
    ap.add_argument('--lento', type=float, default=0.0)
    ap.add_argument('--workers', type=int, default=20)
    args = ap.parse_args()

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as srv:
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind(('0.0.0.0', args.port))
        srv.listen(1024)
        extra = f' workers={args.workers}' if args.modo == 'pool' else ''
        print(f'[{args.modo}] pid={os.getpid()} puerto {args.port} '
              f'lento={args.lento}s{extra}', flush=True)
        servir(args.modo, srv, args.lento, args.workers)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('\nServidor detenido')
