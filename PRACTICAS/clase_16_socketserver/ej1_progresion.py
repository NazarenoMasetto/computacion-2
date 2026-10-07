#!/usr/bin/env python3
"""Ejercicio 1: la progresión de socketserver, paso a paso.

Cada --paso corresponde a una sección del ejercicio 1:

    minimo      1.1  eco de 5 líneas (imprime type(self.request) e id(self))
    lento       1.3  handle() con sleep(3) para medir concurrencia
    recv        1.4  BaseRequestHandler + recv(1024): sin framing
    stream      1.4  StreamRequestHandler iterando rfile: framing por líneas
    contador-handler   1.5  contador en el handler (siempre da 1)
    contador-servidor  1.5  contador en el servidor, con Lock
    contador-sinlock   1.5  contador en el servidor, SIN Lock
    errores     1.6  setup/handle/finish con prints; "CRASH" lanza excepción

Opciones:
    --servidor {secuencial,threading,forking}   (default: secuencial)
    --reuse          activa allow_reuse_address (1.2)
    --sin-super      setup() no llama a super().setup() (1.6, pregunta 18)
    --port N         puerto (default 8080)

Ejemplos:
    python3 ej1_progresion.py --paso minimo
    python3 ej1_progresion.py --paso lento --servidor threading --reuse
"""
import argparse
import os
import socketserver
import threading
import time
import traceback


# ---------------------------------------------------------------
# 1.1 El mínimo
# ---------------------------------------------------------------

class Minimo(socketserver.BaseRequestHandler):
    """Eco en mayúsculas. Muestra qué es self.request y que cada conexión
    crea una instancia nueva."""

    def handle(self):
        print(f'type(self.request) = {type(self.request)}')
        print(f'id(self) = {id(self)}')
        # Leemos en bucle: handle() corre UNA vez por conexión, así que si
        # el cliente manda tres mensajes, hay que leer tres veces acá adentro.
        while True:
            datos = self.request.recv(1024)
            if not datos:
                break
            self.request.sendall(datos.upper())
        print(f'fin de handle() para {self.client_address}')


# ---------------------------------------------------------------
# 1.3 Concurrencia
# ---------------------------------------------------------------

class Lento(socketserver.BaseRequestHandler):
    """Tarda 3 segundos en responder: sirve para medir si hay paralelismo."""

    def handle(self):
        print(f'atendiendo {self.client_address} en pid={os.getpid()} '
              f'hilo={threading.current_thread().name}')
        time.sleep(3)
        self.request.sendall(f'listo (pid {os.getpid()})\n'.encode())


# ---------------------------------------------------------------
# 1.4 Framing
# ---------------------------------------------------------------

class ConRecv(socketserver.BaseRequestHandler):
    def handle(self):
        datos = self.request.recv(1024)          # ¿esto es una línea? no.
        print(f'recv() devolvió: {datos!r}')
        self.request.sendall(b'recibi: ' + datos)


class ConStream(socketserver.StreamRequestHandler):
    def handle(self):
        for linea in self.rfile:                 # una vuelta = una línea
            print(f'línea: {linea!r}')
            self.wfile.write(b'recibi: ' + linea.strip() + b'\n')


# ---------------------------------------------------------------
# 1.5 Estado
# ---------------------------------------------------------------

class ContadorEnHandler(socketserver.StreamRequestHandler):
    n = 0

    def handle(self):
        # Lee el 0 de la clase y guarda 1 en la INSTANCIA, que muere al cerrar.
        self.n += 1
        self.wfile.write(f'visita {self.n}\n'.encode())


class ContadorEnServidor(socketserver.StreamRequestHandler):
    def handle(self):
        with self.server.lock:
            self.server.visitas += 1
            n = self.server.visitas              # la lectura también adentro
        self.wfile.write(f'visita {n}\n'.encode())


class ContadorSinLock(socketserver.StreamRequestHandler):
    def handle(self):
        # Leer, sumar y guardar NO es atómico: puede perderse una cuenta.
        self.server.visitas += 1
        self.wfile.write(f'visita {self.server.visitas}\n'.encode())


# ---------------------------------------------------------------
# 1.6 Errores
# ---------------------------------------------------------------

class ConErrores(socketserver.StreamRequestHandler):
    sin_super = False

    def setup(self):
        print(f'  setup()  {self.client_address}')
        if not self.sin_super:
            super().setup()                      # crea rfile/wfile

    def handle(self):
        print(f'  handle() {self.client_address}')
        for linea in self.rfile:
            if linea.strip() == b'CRASH':
                raise RuntimeError('el cliente pidió que explote')
            self.wfile.write(b'ok\n')

    def finish(self):
        print(f'  finish() {self.client_address}')
        if not self.sin_super:
            super().finish()


# ---------------------------------------------------------------
# Servidores
# ---------------------------------------------------------------

def crear_clase_servidor(tipo, reuse):
    """Arma la clase servidor según la concurrencia pedida."""
    base = {
        'secuencial': socketserver.TCPServer,
        'threading': socketserver.ThreadingTCPServer,
        'forking': socketserver.ForkingTCPServer,
    }[tipo]

    class Servidor(base):
        allow_reuse_address = reuse
        daemon_threads = True

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.visitas = 0
            self.lock = threading.Lock()

        def handle_error(self, request, client_address):
            ultima = traceback.format_exc().strip().splitlines()[-1]
            print(f'  handle_error({client_address}): {ultima}')

    return Servidor


HANDLERS = {
    'minimo': Minimo,
    'lento': Lento,
    'recv': ConRecv,
    'stream': ConStream,
    'contador-handler': ContadorEnHandler,
    'contador-servidor': ContadorEnServidor,
    'contador-sinlock': ContadorSinLock,
    'errores': ConErrores,
}


def main():
    parser = argparse.ArgumentParser(description='Ejercicio 1 de la clase 16')
    parser.add_argument('--paso', choices=HANDLERS, default='minimo')
    parser.add_argument('--servidor', default='secuencial',
                        choices=['secuencial', 'threading', 'forking'])
    parser.add_argument('--reuse', action='store_true',
                        help='allow_reuse_address = True')
    parser.add_argument('--sin-super', action='store_true',
                        help='no llamar a super().setup() en el paso errores')
    parser.add_argument('--port', type=int, default=8080)
    args = parser.parse_args()

    Handler = HANDLERS[args.paso]
    ConErrores.sin_super = args.sin_super
    Servidor = crear_clase_servidor(args.servidor, args.reuse)

    with Servidor(('0.0.0.0', args.port), Handler) as srv:
        print(f'[{args.paso}] {args.servidor} en :{args.port} '
              f'(reuse={args.reuse}, pid={os.getpid()})', flush=True)
        try:
            srv.serve_forever()
        except KeyboardInterrupt:
            print('\nServidor detenido')


if __name__ == '__main__':
    main()
