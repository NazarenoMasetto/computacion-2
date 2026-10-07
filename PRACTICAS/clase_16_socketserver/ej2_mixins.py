#!/usr/bin/env python3
"""Ejercicio 2 (obligatorio), partes A y B: leer los mixins y ver el MRO.

Sin argumentos imprime el análisis (métodos de cada mixin, MRO de Bien y
Mal, quién provee process_request).

Con --servir {bien,mal} levanta un servidor lento (sleep 3) con esa clase,
para medir con cliente_medir.py cuál atiende en paralelo.

Uso:
    python3 ej2_mixins.py
    python3 ej2_mixins.py --servir bien [--port 8080]
    python3 ej2_mixins.py --servir mal  [--port 8080]
"""
import argparse
import inspect
import socketserver
import threading
import time


class Bien(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True
    daemon_threads = True


class Mal(socketserver.TCPServer, socketserver.ThreadingMixIn):
    allow_reuse_address = True
    daemon_threads = True


class Lento(socketserver.BaseRequestHandler):
    def handle(self):
        print(f'atiendo {self.client_address} en {threading.current_thread().name}',
              flush=True)
        time.sleep(3)
        self.request.sendall(b'listo\n')


def metodos_propios(clase):
    """Métodos definidos en la propia clase (no heredados)."""
    return [n for n, v in vars(clase).items() if inspect.isfunction(v)]


def quien_provee(clase, metodo):
    return next(k.__name__ for k in clase.__mro__ if metodo in k.__dict__)


def analisis():
    print('=== Parte A: los mixins ===')
    for mixin in (socketserver.ThreadingMixIn, socketserver.ForkingMixIn):
        print(f'{mixin.__name__}: {metodos_propios(mixin)}')

    print('\nBaseServer.process_request:')
    print(inspect.getsource(socketserver.BaseServer.process_request))
    print('ThreadingMixIn.process_request:')
    print(inspect.getsource(socketserver.ThreadingMixIn.process_request))

    # ThreadingTCPServer no tiene cuerpo propio: es "pass"
    print('Código propio de ThreadingTCPServer:',
          metodos_propios(socketserver.ThreadingTCPServer) or 'ninguno (pass)')
    print(inspect.getsource(socketserver.ThreadingTCPServer))

    print('=== Parte B: el orden ===')
    for C in (Bien, Mal):
        print(C.__name__, [k.__name__ for k in C.__mro__][:4])
    for C in (Bien, Mal):
        print(f'{C.__name__}: process_request viene de '
              f'{quien_provee(C, "process_request")}')


def main():
    parser = argparse.ArgumentParser(description='Ejercicio 2 A/B')
    parser.add_argument('--servir', choices=['bien', 'mal'])
    parser.add_argument('--port', type=int, default=8080)
    args = parser.parse_args()

    if not args.servir:
        analisis()
        return

    Clase = Bien if args.servir == 'bien' else Mal
    # Ojo: Mal NO tira ningún error. Arranca y "anda", pero secuencial.
    with Clase(('0.0.0.0', args.port), Lento) as srv:
        print(f'{Clase.__name__} escuchando en :{args.port}', flush=True)
        try:
            srv.serve_forever()
        except KeyboardInterrupt:
            print('\nServidor detenido')


if __name__ == '__main__':
    main()
