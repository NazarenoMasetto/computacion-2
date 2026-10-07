#!/usr/bin/env python3
"""Adicional: el patrón self-pipe (clase 6) integrado con selectors.

El handler de SIGINT no hace nada "real": solo escribe un byte en un pipe.
El extremo de lectura está registrado en el selector, así que Ctrl+C se
convierte en un evento más del bucle y se atiende en un punto seguro
(no en medio de un accept() o de un send()).

Uso:
    python3 self_pipe.py [--port 8080]
    nc localhost 8080      y después Ctrl+C (o kill -INT <pid>) en el servidor
"""
import argparse
import os
import selectors
import signal
import socket


def main():
    parser = argparse.ArgumentParser(description='self-pipe con selectors')
    parser.add_argument('--port', type=int, default=8080)
    args = parser.parse_args()

    sel = selectors.DefaultSelector()
    pipe_r, pipe_w = os.pipe()
    os.set_blocking(pipe_r, False)
    os.set_blocking(pipe_w, False)

    def al_recibir_senal(signum, _frame):
        # Lo mínimo dentro del handler: avisar por el pipe y volver.
        try:
            os.write(pipe_w, bytes([signum]))
        except BlockingIOError:
            pass                    # pipe lleno: ya hay un aviso pendiente

    signal.signal(signal.SIGINT, al_recibir_senal)
    signal.signal(signal.SIGTERM, al_recibir_senal)

    servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    servidor.bind(('0.0.0.0', args.port))
    servidor.listen(128)
    servidor.setblocking(False)
    sel.register(servidor, selectors.EVENT_READ, 'aceptar')
    sel.register(pipe_r, selectors.EVENT_READ, 'senal')
    print(f'Eco en :{args.port} (pid {os.getpid()}). Ctrl+C para salir.', flush=True)

    clientes = set()
    corriendo = True
    while corriendo:
        for clave, _ in sel.select():
            if clave.data == 'senal':
                senales = os.read(pipe_r, 64)
                nombre = signal.Signals(senales[0]).name
                print(f'\nSeñal {nombre} recibida como evento del loop', flush=True)
                corriendo = False
            elif clave.data == 'aceptar':
                conn, direccion = servidor.accept()
                conn.setblocking(False)
                sel.register(conn, selectors.EVENT_READ, 'cliente')
                clientes.add(conn)
                print(f'+ cliente {direccion}', flush=True)
            else:
                conn = clave.fileobj
                datos = conn.recv(4096)
                if datos:
                    conn.sendall(datos)
                else:
                    sel.unregister(conn)
                    clientes.discard(conn)
                    conn.close()

    # Cierre ordenado, fuera de cualquier handler de señal
    for conn in clientes:
        try:
            conn.sendall(b'El servidor se apaga. Chau.\n')
        except OSError:
            pass
        sel.unregister(conn)
        conn.close()
    sel.close()
    servidor.close()
    os.close(pipe_r)
    os.close(pipe_w)
    print(f'Cerré {len(clientes)} clientes de forma ordenada.')


if __name__ == '__main__':
    main()
