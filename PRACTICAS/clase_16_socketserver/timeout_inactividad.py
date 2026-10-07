#!/usr/bin/env python3
"""Adicional: timeout de inactividad con StreamRequestHandler.timeout.

El atributo de clase `timeout` hace que setup() llame a settimeout() sobre
el socket. Si el cliente no manda nada en ese tiempo, la lectura de rfile
lanza TimeoutError; lo atrapamos y llamamos a nuestro handle_timeout().

Uso:
    python3 timeout_inactividad.py [--timeout 10] [--port 8080]
    nc localhost 8080        (y no escribas nada)
"""
import argparse
import socketserver


class HandlerConTimeout(socketserver.StreamRequestHandler):
    timeout = 10

    def handle(self):
        self.wfile.write(f'Eco. Te corto si no escribis en {self.timeout}s\n'.encode())
        try:
            for linea in self.rfile:
                self.wfile.write(linea)
        except TimeoutError:
            self.handle_timeout()

    def handle_timeout(self):
        """Se llama cuando el cliente estuvo inactivo demasiado tiempo."""
        print(f'timeout: {self.client_address} inactivo {self.timeout}s', flush=True)
        try:
            self.wfile.write(b'Desconectado por inactividad\n')
        except OSError:
            pass


class Servidor(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True


def main():
    parser = argparse.ArgumentParser(description='Timeout de inactividad')
    parser.add_argument('--timeout', type=float, default=10)
    parser.add_argument('--port', type=int, default=8080)
    args = parser.parse_args()

    HandlerConTimeout.timeout = args.timeout
    with Servidor(('0.0.0.0', args.port), HandlerConTimeout) as srv:
        print(f'Escuchando en :{args.port} (timeout {args.timeout}s)', flush=True)
        try:
            srv.serve_forever()
        except KeyboardInterrupt:
            print('\nServidor detenido')


if __name__ == '__main__':
    main()
