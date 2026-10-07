#!/usr/bin/env python3
"""Ejercicio 2, parte D: efecto de daemon_threads.

Eco por líneas con ThreadingTCPServer. Conectate con nc, dejá el cliente
abierto y cortá el servidor con Ctrl+C:

    python3 ej2_daemon.py --sin-daemon   # se queda colgado esperando al cliente
    python3 ej2_daemon.py                # corta de inmediato

Uso:
    python3 ej2_daemon.py [--sin-daemon] [--port 8080]
"""
import argparse
import socketserver


class Eco(socketserver.StreamRequestHandler):
    def handle(self):
        for linea in self.rfile:
            self.wfile.write(linea)


def main():
    parser = argparse.ArgumentParser(description='Ejercicio 2 D')
    parser.add_argument('--sin-daemon', action='store_true')
    parser.add_argument('--port', type=int, default=8080)
    args = parser.parse_args()

    class Servidor(socketserver.ThreadingTCPServer):
        allow_reuse_address = True
        daemon_threads = not args.sin_daemon

    with Servidor(('0.0.0.0', args.port), Eco) as srv:
        print(f'daemon_threads={Servidor.daemon_threads} en :{args.port}',
              flush=True)
        try:
            srv.serve_forever()
        except KeyboardInterrupt:
            # Al salir del with se llama server_close(), que hace join() de
            # los threads NO daemon: ahí se queda esperando al cliente.
            print('\nCtrl+C recibido, cerrando...', flush=True)
    print('Servidor detenido', flush=True)


if __name__ == '__main__':
    main()
