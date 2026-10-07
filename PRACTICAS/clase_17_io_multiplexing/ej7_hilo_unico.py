#!/usr/bin/env python3
"""Ejercicio 7: el costo del hilo único.

Servidor con selectors donde cada mensaje dispara ~3 millones de sha256
(trabajo de CPU). Tres modos:

    (default)   el trabajo corre en el event loop: congela a todos
    --threads   un thread por cliente, como server_threads.py de la clase 14
    --pool      event loop + ProcessPoolExecutor: el loop no se bloquea
                (la respuesta del 7.4)

Además, si el mensaje es "ping" se responde al instante sin calcular, para
ver si el servidor atiende a otro cliente mientras procesa.

Uso:
    python3 ej7_hilo_unico.py [--threads | --pool] [--port 8080] [--vueltas 3000000]
    Terminal 2:  echo calcular | nc -q5 localhost 8080
    Terminal 3:  echo ping | nc -q1 localhost 8080      (mientras la 2 espera)
"""
import argparse
import concurrent.futures
import hashlib
import selectors
import socket
import threading

VUELTAS = 3_000_000


def trabajo_pesado(datos):
    h = datos
    for _ in range(VUELTAS):
        h = hashlib.sha256(h).digest()
    return h.hex().encode() + b'\n'


def responder_a(datos):
    """ping se contesta enseguida; cualquier otra cosa, con el cálculo."""
    if datos.strip() == b'ping':
        return b'pong\n'
    return trabajo_pesado(datos)


# ---------------------------------------------------------------
# Modo event loop (con o sin pool de procesos)
# ---------------------------------------------------------------

def servir_event_loop(servidor, usar_pool, vueltas):
    sel = selectors.DefaultSelector()
    pool = concurrent.futures.ProcessPoolExecutor(
        initializer=_fijar_vueltas, initargs=(vueltas,)) if usar_pool else None
    # El pool avisa que terminó por un socketpair (self-pipe): así el
    # resultado entra al loop como un evento más, sin threads extra.
    despertador_r, despertador_w = socket.socketpair()
    despertador_r.setblocking(False)
    terminados = []                  # (conn, respuesta) listos para enviar
    lock_terminados = threading.Lock()

    servidor.setblocking(False)
    sel.register(servidor, selectors.EVENT_READ, 'aceptar')
    sel.register(despertador_r, selectors.EVENT_READ, 'despertar')

    def al_terminar(conn, futuro):
        # Corre en un thread interno del executor: solo encola y despierta.
        with lock_terminados:
            terminados.append((conn, futuro.result()))
        despertador_w.send(b'x')

    try:
        while True:
            for clave, _ in sel.select():
                if clave.data == 'aceptar':
                    conn, _ = servidor.accept()
                    sel.register(conn, selectors.EVENT_READ, 'cliente')
                elif clave.data == 'despertar':
                    despertador_r.recv(4096)
                    with lock_terminados:
                        listos = terminados[:]
                        terminados.clear()
                    for conn, respuesta in listos:
                        conn.sendall(respuesta)
                else:
                    conn = clave.fileobj
                    datos = conn.recv(4096)
                    if not datos:
                        sel.unregister(conn)
                        conn.close()
                    elif usar_pool and datos.strip() != b'ping':
                        futuro = pool.submit(trabajo_pesado, datos)
                        futuro.add_done_callback(
                            lambda f, c=conn: al_terminar(c, f))
                    else:
                        # Sin pool: el cálculo corre ACÁ y nadie más es atendido
                        conn.sendall(responder_a(datos))
    finally:
        sel.close()
        if pool:
            pool.shutdown(cancel_futures=True)


def _fijar_vueltas(vueltas):
    global VUELTAS
    VUELTAS = vueltas


# ---------------------------------------------------------------
# Modo un thread por cliente (como la clase 14)
# ---------------------------------------------------------------

def atender_thread(conn):
    with conn:
        while datos := conn.recv(4096):
            conn.sendall(responder_a(datos))


def servir_threads(servidor):
    while True:
        conn, _ = servidor.accept()
        threading.Thread(target=atender_thread, args=(conn,), daemon=True).start()


def main():
    global VUELTAS
    parser = argparse.ArgumentParser(description='El costo del hilo único')
    modo = parser.add_mutually_exclusive_group()
    modo.add_argument('--threads', action='store_true')
    modo.add_argument('--pool', action='store_true')
    parser.add_argument('--port', type=int, default=8080)
    parser.add_argument('--vueltas', type=int, default=VUELTAS)
    args = parser.parse_args()
    VUELTAS = args.vueltas

    servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    servidor.bind(('0.0.0.0', args.port))
    servidor.listen(128)
    nombre = 'threads' if args.threads else ('event loop + pool' if args.pool
                                             else 'event loop puro')
    print(f'[{nombre}] escuchando en :{args.port}', flush=True)
    try:
        if args.threads:
            servir_threads(servidor)
        else:
            servir_event_loop(servidor, args.pool, args.vueltas)
    except KeyboardInterrupt:
        print('\nServidor detenido')
    finally:
        servidor.close()


if __name__ == '__main__':
    main()
