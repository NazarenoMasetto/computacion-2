#!/usr/bin/env python3
"""Adicional: servidor de threads con cierre ordenado (graceful shutdown).

Al recibir Ctrl+C o SIGTERM deja de aceptar, espera a que los clientes
actuales terminen (hasta --gracia segundos) y recién ahí sale.

Uso:
    python3 ad_cierre_ordenado.py [--port 8080] [--lento SEG] [--gracia 10]
"""
import argparse
import signal
import socket
import threading
import time

apagando = threading.Event()     # clase 11: señal entre threads


def atender(conn, lento):
    try:
        with conn:
            conn.settimeout(1.0)
            if lento:
                time.sleep(lento)
            while True:
                try:
                    datos = conn.recv(4096)
                except TimeoutError:
                    if apagando.is_set():
                        break        # cliente inactivo y estamos cerrando
                    continue
                if not datos:
                    break
                conn.sendall(datos)
    except (ConnectionResetError, BrokenPipeError):
        pass


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--port', type=int, default=8080)
    ap.add_argument('--lento', type=float, default=0.0)
    ap.add_argument('--gracia', type=float, default=10.0)
    args = ap.parse_args()

    # SIGTERM se trata igual que Ctrl+C
    signal.signal(signal.SIGTERM, lambda s, f: apagando.set())
    signal.signal(signal.SIGINT, lambda s, f: apagando.set())

    hilos = []
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as srv:
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind(('0.0.0.0', args.port))
        srv.listen(128)
        srv.settimeout(0.5)      # para revisar el Event periódicamente
        print(f'[ordenado] puerto {args.port} (Ctrl+C para cerrar)', flush=True)
        while not apagando.is_set():
            try:
                conn, _ = srv.accept()
            except (TimeoutError, InterruptedError):
                continue
            conn.settimeout(None)
            h = threading.Thread(target=atender, args=(conn, args.lento))  # NO daemon
            h.start()
            hilos.append(h)
            hilos = [x for x in hilos if x.is_alive()]

    # ya no aceptamos más: esperar a los que están
    vivos = [h for h in hilos if h.is_alive()]
    print(f'Cerrando: espero a {len(vivos)} cliente(s), máximo {args.gracia}s', flush=True)
    limite = time.monotonic() + args.gracia
    for h in vivos:
        h.join(max(0.0, limite - time.monotonic()))
    quedan = sum(h.is_alive() for h in vivos)
    if quedan:
        print(f'Timeout: {quedan} cliente(s) no terminaron; salgo igual', flush=True)
        # no son daemon: hay que soltarlos, así que el proceso termina a la fuerza
        import os
        os._exit(1)
    print('Todos los clientes terminaron. Chau.', flush=True)


if __name__ == '__main__':
    main()
