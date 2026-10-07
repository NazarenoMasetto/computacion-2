#!/usr/bin/env python3
"""Ej 4: contador de clientes activos con y sin lock.

Uso:
    python3 ej4_threads_race.py [--port 8080] [--sin-lock] [--pausa 0.0001]

Al cortar con Ctrl+C (o kill -INT) imprime el contador: con todos los
clientes ya desconectados debería ser 0.
"""
import argparse
import socket
import threading
import time

clientes_activos = 0
total_atendidos = 0
lock = threading.Lock()
ARGS = None


def modificar(delta):
    """clientes_activos += delta, separando lectura y escritura a propósito."""
    global clientes_activos
    leido = clientes_activos            # LOAD
    if ARGS.pausa:
        time.sleep(ARGS.pausa)          # agranda la ventana de la carrera
    clientes_activos = leido + delta    # STORE


def cambiar(delta):
    if ARGS.sin_lock:
        modificar(delta)
    else:
        with lock:
            modificar(delta)


def atender(conn):
    global total_atendidos
    cambiar(+1)
    try:
        with conn:
            while (datos := conn.recv(4096)):
                conn.sendall(datos)
    except (ConnectionResetError, BrokenPipeError):
        pass
    finally:
        cambiar(-1)
        with lock:
            total_atendidos += 1


def main():
    global ARGS
    ap = argparse.ArgumentParser()
    ap.add_argument('--port', type=int, default=8080)
    ap.add_argument('--sin-lock', action='store_true')
    ap.add_argument('--pausa', type=float, default=0.0)
    ARGS = ap.parse_args()

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as srv:
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind(('0.0.0.0', ARGS.port))
        srv.listen(1024)
        print(f'[threads] puerto {ARGS.port} lock={"NO" if ARGS.sin_lock else "sí"} '
              f'pausa={ARGS.pausa}', flush=True)
        while True:
            conn, _ = srv.accept()
            threading.Thread(target=atender, args=(conn,), daemon=True).start()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        time.sleep(0.2)
        print(f'\nAtendidos: {total_atendidos}  clientes_activos al final: '
              f'{clientes_activos} {"(OK)" if clientes_activos == 0 else "(RACE!)"}')
