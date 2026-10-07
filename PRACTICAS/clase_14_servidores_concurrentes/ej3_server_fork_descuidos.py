#!/usr/bin/env python3
"""Ej 3: server_fork con los "tres descuidos" activables por opción.

Uso:
    python3 ej3_server_fork_descuidos.py [--port 8080] [--lento SEG] --descuido X

Descuidos (X):
    ninguno      versión correcta (default)
    sin-close    parte A: el padre NO cierra conn (CPython igual lo cierra por GC)
    guardar      parte A2: el padre guarda conn en una lista (fd filtrado de verdad)
    sin-handler  parte B: sin handler de SIGCHLD -> zombies
    sin-bucle    parte C: el cosechador recoge UN hijo por señal
    sig-ign      parte D: SIGCHLD = SIG_IGN, el kernel cosecha
"""
import argparse
import os
import signal
import socket
import time

conexiones_abiertas = []      # parte A2: referencias que sobreviven


def cosechar_bien(signum, frame):
    """Con bucle: recoge todos los hijos terminados."""
    while True:
        try:
            pid, _ = os.waitpid(-1, os.WNOHANG)
        except ChildProcessError:
            return
        if pid == 0:
            return


def cosechar_sin_bucle(signum, frame):
    """SIN bucle: un hijo por señal. Si dos SIGCHLD se fusionan, queda un zombie."""
    try:
        os.waitpid(-1, os.WNOHANG)
    except ChildProcessError:
        pass


def atender(conn, lento):
    if lento:
        time.sleep(lento)
    while (datos := conn.recv(4096)):
        conn.sendall(datos)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--port', type=int, default=8080)
    ap.add_argument('--lento', type=float, default=0.0)
    ap.add_argument('--descuido', default='ninguno',
                    choices=['ninguno', 'sin-close', 'guardar', 'sin-handler',
                             'sin-bucle', 'sig-ign'])
    args = ap.parse_args()
    d = args.descuido

    if d == 'sin-bucle':
        signal.signal(signal.SIGCHLD, cosechar_sin_bucle)
    elif d == 'sig-ign':
        signal.signal(signal.SIGCHLD, signal.SIG_IGN)
    elif d != 'sin-handler':
        signal.signal(signal.SIGCHLD, cosechar_bien)
    # con 'sin-handler' no se instala nada: los hijos quedan zombies

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as srv:
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind(('0.0.0.0', args.port))
        srv.listen(128)
        print(f'[fork:{d}] PADRE pid={os.getpid()} puerto {args.port}', flush=True)
        while True:
            try:
                conn, _ = srv.accept()
            except InterruptedError:
                continue
            pid = os.fork()
            if pid == 0:
                # ---- HIJO ----
                srv.close()
                try:
                    atender(conn, args.lento)
                except (ConnectionResetError, BrokenPipeError):
                    pass
                finally:
                    conn.close()
                    os._exit(0)
            # ---- PADRE ----
            if d == 'guardar':
                conexiones_abiertas.append(conn)   # la referencia sobrevive
            elif d == 'sin-close':
                pass                               # conn.close() "olvidado"
            else:
                conn.close()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('\nServidor detenido')
