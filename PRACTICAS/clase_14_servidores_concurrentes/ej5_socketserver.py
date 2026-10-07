#!/usr/bin/env python3
"""Ej 5: servidor eco con socketserver (threads o fork).

Uso:
    python3 ej5_socketserver.py [--port 8080] [--lento SEG] [--forking]
"""
import argparse
import socketserver
import time

LENTO = 0.0


class EchoHandler(socketserver.StreamRequestHandler):
    def handle(self):
        if LENTO:
            time.sleep(LENTO)
        # rfile es un archivo con buffer: read1() devuelve lo que haya
        # (readline() también serviría, y resuelve el framing por líneas)
        while (datos := self.rfile.read1(4096)):
            self.wfile.write(datos)


class Servidor(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True
    request_queue_size = 128


class ServidorFork(socketserver.ForkingTCPServer):
    allow_reuse_address = True
    request_queue_size = 128


def main():
    global LENTO
    ap = argparse.ArgumentParser()
    ap.add_argument('--port', type=int, default=8080)
    ap.add_argument('--lento', type=float, default=0.0)
    ap.add_argument('--forking', action='store_true')
    args = ap.parse_args()
    LENTO = args.lento

    clase = ServidorFork if args.forking else Servidor
    with clase(('0.0.0.0', args.port), EchoHandler) as srv:
        print(f'[{clase.__name__}] puerto {args.port} lento={LENTO}', flush=True)
        srv.serve_forever()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('\nServidor detenido')
