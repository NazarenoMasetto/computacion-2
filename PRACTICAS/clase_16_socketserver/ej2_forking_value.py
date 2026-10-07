#!/usr/bin/env python3
"""Ejercicio 2, parte C: contador con ForkingTCPServer.

Con un int común cada hijo incrementa SU copia (fork copia la memoria) y
el cliente siempre ve "visita 1". Con multiprocessing.Value creado en el
__init__ del servidor (antes de cualquier fork), todos los hijos comparten
la misma memoria y el contador funciona.

Uso:
    python3 ej2_forking_value.py [--port 8080]            # int: falla
    python3 ej2_forking_value.py --value [--port 8080]    # Value: anda
"""
import argparse
import multiprocessing
import os
import socketserver


class Contador(socketserver.StreamRequestHandler):
    def handle(self):
        if self.server.usar_value:
            # get_lock() es el Lock de multiprocessing que trae el Value
            with self.server.visitas.get_lock():
                self.server.visitas.value += 1
                n = self.server.visitas.value
        else:
            self.server.visitas += 1          # se incrementa en la copia del hijo
            n = self.server.visitas
        self.wfile.write(f'visita {n} (pid {os.getpid()})\n'.encode())


class Servidor(socketserver.ForkingTCPServer):
    allow_reuse_address = True

    def __init__(self, *args, usar_value=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.usar_value = usar_value
        # Se crea en el PADRE, antes de forkear: los hijos heredan el mapeo
        # de memoria compartida. Creado en el handler, ya sería tarde.
        self.visitas = multiprocessing.Value('i', 0) if usar_value else 0


def main():
    parser = argparse.ArgumentParser(description='Ejercicio 2 C')
    parser.add_argument('--value', action='store_true',
                        help='usar multiprocessing.Value')
    parser.add_argument('--port', type=int, default=8080)
    args = parser.parse_args()

    with Servidor(('0.0.0.0', args.port), Contador, usar_value=args.value) as srv:
        modo = 'multiprocessing.Value' if args.value else 'int común'
        print(f'ForkingTCPServer en :{args.port} con {modo}', flush=True)
        try:
            srv.serve_forever()
        except KeyboardInterrupt:
            print('\nServidor detenido')


if __name__ == '__main__':
    main()
