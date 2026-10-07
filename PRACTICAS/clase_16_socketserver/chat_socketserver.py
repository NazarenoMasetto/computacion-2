#!/usr/bin/env python3
"""Adicional: el chat.py de la clase 17, reescrito con ThreadingTCPServer.

Un thread por cliente. La lista de clientes vive en el servidor y se
protege con un Lock, porque cada handler la recorre desde su thread.

Uso:
    python3 chat_socketserver.py [--port 8080]
    nc localhost 8080       (desde varias terminales)
"""
import argparse
import socketserver
import threading


class ChatHandler(socketserver.StreamRequestHandler):

    def setup(self):
        super().setup()
        self.apodo = f'{self.client_address[0]}:{self.client_address[1]}'
        with self.server.lock:
            self.server.clientes.add(self)
            total = len(self.server.clientes)
        print(f'+ {self.apodo}  ({total} conectados)', flush=True)

    def finish(self):
        with self.server.lock:
            self.server.clientes.discard(self)
            total = len(self.server.clientes)
        print(f'- {self.apodo}  ({total} conectados)', flush=True)
        self.server.difundir(f'* se fue {self.apodo}\n'.encode())
        try:
            super().finish()
        except OSError:
            pass

    def handle(self):
        self.wfile.write(b'Bienvenido al chat. Escribi y presiona Enter.\n')
        self.server.difundir(f'* se conecto {self.apodo}\n'.encode(), excepto=self)
        # rfile ya entrega líneas completas: el framing viene resuelto.
        for linea in self.rfile:
            texto = linea.decode('utf-8', 'replace').rstrip('\r\n')
            if texto:
                print(f'  <{self.apodo}> {texto}', flush=True)
                self.server.difundir(f'<{self.apodo}> {texto}\n'.encode(),
                                     excepto=self)


class ServidorChat(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.clientes = set()
        self.lock = threading.Lock()

    def difundir(self, mensaje, excepto=None):
        with self.lock:
            destinos = [c for c in self.clientes if c is not excepto]
        for c in destinos:
            try:
                # Ojo: si c es lento, este sendall bloquea SOLO a este thread
                # (el del emisor), no a todo el servidor como en un event loop.
                c.wfile.write(mensaje)
            except OSError:
                pass            # se desconectó: su finish() lo saca de la lista


def main():
    parser = argparse.ArgumentParser(description='Chat con socketserver')
    parser.add_argument('--port', type=int, default=8080)
    args = parser.parse_args()
    with ServidorChat(('0.0.0.0', args.port), ChatHandler) as srv:
        print(f'Chat (threads) escuchando en :{args.port}', flush=True)
        try:
            srv.serve_forever()
        except KeyboardInterrupt:
            print('\nChat detenido')


if __name__ == '__main__':
    main()
