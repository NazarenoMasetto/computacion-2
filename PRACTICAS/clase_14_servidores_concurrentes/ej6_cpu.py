#!/usr/bin/env python3
"""Ej 6: servidor eco que hace trabajo CPU-bound real por cliente.

Uso:
    python3 ej6_cpu.py --modo threads|fork [--port 8080] [--n 2000000]
    python3 benchmark.py --clientes 10
"""
import argparse
import os
import signal
import socket
import sys
import threading

N = 2_000_000


def trabajo_cpu(n):
    """CPU-bound de verdad: no libera el GIL."""
    total = 0
    for i in range(n):
        total += i * i
    return total


def atender(conn):
    try:
        trabajo_cpu(N)
        with conn:
            while (datos := conn.recv(4096)):
                conn.sendall(datos)
    except (ConnectionResetError, BrokenPipeError):
        pass


def main():
    global N
    ap = argparse.ArgumentParser()
    ap.add_argument('--modo', choices=['threads', 'fork'], default='threads')
    ap.add_argument('--port', type=int, default=8080)
    ap.add_argument('--n', type=int, default=N)
    args = ap.parse_args()
    N = args.n

    gil = sys._is_gil_enabled() if hasattr(sys, '_is_gil_enabled') else True
    if args.modo == 'fork':
        signal.signal(signal.SIGCHLD, signal.SIG_IGN)   # el kernel cosecha
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as srv:
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind(('0.0.0.0', args.port))
        srv.listen(128)
        print(f'[cpu:{args.modo}] puerto {args.port} n={N} nproc={os.cpu_count()} '
              f'{"con GIL" if gil else "SIN GIL"}', flush=True)
        while True:
            try:
                conn, _ = srv.accept()
            except InterruptedError:
                continue
            if args.modo == 'threads':
                threading.Thread(target=atender, args=(conn,), daemon=True).start()
            elif os.fork() == 0:
                srv.close()
                atender(conn)
                os._exit(0)
            else:
                conn.close()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('\nServidor detenido')
