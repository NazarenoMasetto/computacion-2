#!/usr/bin/env python3
"""Ejercicio 4: servidor de comandos extendido.

Sobre el comandos.py de la clase se agregan:
  - NICK <nombre>      apodo por cliente
  - BROADCAST <texto>  mensaje a todos los conectados
  - manejo de clientes que se desconectan mientras se les escribe
  - timeout de inactividad (default 30 s)

Comandos: TIME, ECHO <texto>, QUIEN, CONTADOR, NICK <nombre>,
          BROADCAST <texto>, AYUDA, QUIT

Uso:
    python3 comandos.py [--port 8080] [--timeout 30]
    nc localhost 8080
"""
import argparse
import socketserver
import threading
import time


class Handler(socketserver.StreamRequestHandler):
    # StreamRequestHandler aplica esto con settimeout() en setup():
    # si el cliente no manda nada en ese tiempo, la lectura lanza TimeoutError.
    timeout = 30

    def setup(self):
        super().setup()               # imprescindible: crea rfile/wfile
        # El apodo es de ESTA conexión: vive en el handler, que dura lo mismo
        # que la conexión. El servidor guarda referencia a los handlers
        # para que los demás (QUIEN, BROADCAST) puedan verlo y escribirle.
        self.nick = f'{self.client_address[0]}:{self.client_address[1]}'
        # Dos threads pueden escribirle a este cliente a la vez (el suyo y el
        # de un BROADCAST ajeno): este lock evita que se mezclen las líneas.
        self.lock_escritura = threading.Lock()
        with self.server.lock:
            self.server.conexiones += 1
            self.server.clientes.add(self)

    def finish(self):
        with self.server.lock:
            self.server.clientes.discard(self)
        try:
            super().finish()
        except OSError:
            pass                      # el cliente ya no está: nada que flushear

    def responder(self, texto):
        """Escribe una línea a ESTE cliente. Devuelve False si ya se fue."""
        try:
            with self.lock_escritura:
                self.wfile.write((texto + '\n').encode())
            return True
        except OSError:               # BrokenPipe, ConnectionReset, etc.
            return False

    def broadcast(self, texto):
        # Copiamos la lista bajo lock y escribimos AFUERA: si un cliente es
        # lento no queremos tener el lock global tomado mientras tanto.
        with self.server.lock:
            destinos = list(self.server.clientes)
        enviados = 0
        for cliente in destinos:
            # Si se desconectó justo ahora, responder() devuelve False y
            # seguimos con los demás; su propio finish() lo saca del set.
            if cliente.responder(f'[{self.nick}] {texto}'):
                enviados += 1
        return enviados

    def handle(self):
        self.responder('Servidor de comandos. Escribí AYUDA.')
        try:
            for linea in self.rfile:                    # framing por líneas
                if not self.procesar(linea):
                    return
        except TimeoutError:
            self.responder(f'Desconectado por inactividad ({self.timeout}s)')
            print(f'timeout: {self.nick}', flush=True)
        except ConnectionResetError:
            pass

    def procesar(self, linea):
        """Ejecuta un comando. Devuelve False si hay que cerrar."""
        partes = linea.decode('utf-8', 'replace').strip().split(maxsplit=1)
        if not partes:
            return True
        cmd, resto = partes[0].upper(), (partes[1] if len(partes) > 1 else '')

        if cmd == 'TIME':
            self.responder(time.strftime('%Y-%m-%d %H:%M:%S'))
        elif cmd == 'ECHO':
            self.responder(resto)
        elif cmd == 'QUIEN':
            with self.server.lock:
                nicks = sorted(c.nick for c in self.server.clientes)
            self.responder(f'{len(nicks)} conectados: ' + ', '.join(nicks))
        elif cmd == 'CONTADOR':
            with self.server.lock:
                n = self.server.conexiones
            self.responder(f'Conexiones totales desde el arranque: {n}')
        elif cmd == 'NICK':
            if not resto:
                self.responder('Uso: NICK <nombre>')
            else:
                with self.server.lock:     # QUIEN lo lee desde otro thread
                    self.nick = resto
                self.responder(f'Ahora sos {resto}')
        elif cmd == 'BROADCAST':
            n = self.broadcast(resto)
            self.responder(f'(enviado a {n} clientes)')
        elif cmd == 'AYUDA':
            self.responder('TIME | ECHO <texto> | QUIEN | CONTADOR | '
                           'NICK <nombre> | BROADCAST <texto> | QUIT')
        elif cmd == 'QUIT':
            self.responder('Chau')
            return False
        else:
            self.responder(f'Comando desconocido: {cmd}')
        return True


class Servidor(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True
    request_queue_size = 1024         # backlog grande para el ejercicio 5

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.conexiones = 0
        self.clientes = set()         # handlers activos (tienen el socket)
        self.lock = threading.Lock()


def main():
    parser = argparse.ArgumentParser(description='Servidor de comandos')
    parser.add_argument('--port', type=int, default=8080)
    parser.add_argument('--timeout', type=float, default=30,
                        help='segundos de inactividad antes de desconectar')
    args = parser.parse_args()

    Handler.timeout = args.timeout
    with Servidor(('0.0.0.0', args.port), Handler) as srv:
        print(f'Escuchando en 0.0.0.0:{args.port} (timeout {args.timeout}s)',
              flush=True)
        try:
            srv.serve_forever()
        except KeyboardInterrupt:
            print('\nServidor detenido')


if __name__ == '__main__':
    main()
