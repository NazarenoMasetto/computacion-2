#!/usr/bin/env python3
"""Ejercicio 3: socketserver con UDP.

Igual que eco_udp.py de la clase, pero imprime type(self.request) y permite
probar ThreadingUDPServer con un handler lento.

Uso:
    python3 ej3_udp.py [--port 8080]                 # BaseRequestHandler
    python3 ej3_udp.py --files [--port 8080]         # DatagramRequestHandler
    python3 ej3_udp.py --lento [--threading]         # handler que tarda 2s
    python3 ej3_udp.py --cliente "hola" [-n 3]       # cliente de prueba

Probar también con:  echo hola | nc -u -w1 localhost 8080
"""
import argparse
import socket
import socketserver
import threading
import time


class EchoUDPCrudo(socketserver.BaseRequestHandler):
    lento = False

    def handle(self):
        print(f'type(self.request) = {type(self.request)}', flush=True)
        datos, sock = self.request          # tupla (bytes, socket del servidor)
        print(f'{self.client_address}: {datos!r} '
              f'[{threading.current_thread().name}]', flush=True)
        if self.lento:
            time.sleep(2)
        # El socket UDP no está conectado a nadie: hay que decir a quién va.
        sock.sendto(datos.upper(), self.client_address)


class EchoUDPFiles(socketserver.DatagramRequestHandler):
    def handle(self):
        datos = self.rfile.read()
        print(f'{self.client_address}: {datos!r}', flush=True)
        self.wfile.write(datos.upper())     # se envía en finish()


def cliente(texto, puerto, n):
    """Manda n datagramas a la vez (desde n sockets) y mide las respuestas."""
    t0 = time.perf_counter()
    socks = []
    for i in range(n):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(10)
        s.sendto(f'{texto} {i + 1}'.encode(), ('localhost', puerto))
        socks.append(s)
    for s in socks:
        datos, _ = s.recvfrom(2048)
        print(f'{time.perf_counter() - t0:5.2f}s  <- {datos.decode()}')
        s.close()


def main():
    parser = argparse.ArgumentParser(description='Ejercicio 3: UDP')
    parser.add_argument('--files', action='store_true')
    parser.add_argument('--lento', action='store_true')
    parser.add_argument('--threading', action='store_true')
    parser.add_argument('--cliente', metavar='TEXTO')
    parser.add_argument('-n', type=int, default=1)
    parser.add_argument('--port', type=int, default=8080)
    args = parser.parse_args()

    if args.cliente is not None:
        cliente(args.cliente, args.port, args.n)
        return

    Handler = EchoUDPFiles if args.files else EchoUDPCrudo
    EchoUDPCrudo.lento = args.lento
    base = socketserver.ThreadingUDPServer if args.threading else socketserver.UDPServer

    class Servidor(base):
        allow_reuse_address = True
        daemon_threads = True

    with Servidor(('0.0.0.0', args.port), Handler) as srv:
        print(f'{base.__name__} en :{args.port} con {Handler.__name__}', flush=True)
        try:
            srv.serve_forever()
        except KeyboardInterrupt:
            print('\nServidor detenido')


if __name__ == '__main__':
    main()
