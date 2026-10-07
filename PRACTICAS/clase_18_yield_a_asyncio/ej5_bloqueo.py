#!/usr/bin/env python3
"""Ejercicio 5.1: encontrar el bloqueo.

Para no depender de internet, levanta un servidor HTTP local (en un thread)
que tarda 1 segundo en responder cada pedido, y baja 5 veces la misma URL
de tres formas:

    1. urllib.request adentro de una corrutina   -> bloquea el loop (el bug)
    2. urllib.request con asyncio.to_thread()     -> se solapan (parche)
    3. HTTP a mano con asyncio.open_connection()  -> se solapan (I/O async real)

Uso:
    python3 ej5_bloqueo.py [--port 8080]
"""
import argparse
import asyncio
import http.server
import socketserver
import threading
import time
import urllib.request

DEMORA = 1.0
N = 5


class HandlerLento(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        time.sleep(DEMORA)                       # simula un servidor lento
        cuerpo = b'hola desde el servidor lento\n'
        self.send_response(200)
        self.send_header('Content-Length', str(len(cuerpo)))
        self.end_headers()
        self.wfile.write(cuerpo)

    def log_message(self, *args):
        pass                                     # sin ruido en la consola


class ServidorHTTP(socketserver.ThreadingMixIn, http.server.HTTPServer):
    allow_reuse_address = True
    daemon_threads = True


# --- 1. el bug -------------------------------------------------
async def bajar_mal(url):
    return urllib.request.urlopen(url).read()   # bloquea TODO el hilo


# --- 2. parche: mandar lo bloqueante a un thread ---------------
async def bajar_en_thread(url):
    return await asyncio.to_thread(lambda: urllib.request.urlopen(url).read())


# --- 3. I/O asíncrono de verdad --------------------------------
async def bajar_async(host, puerto, ruta='/'):
    reader, writer = await asyncio.open_connection(host, puerto)
    writer.write(f'GET {ruta} HTTP/1.0\r\nHost: {host}\r\n\r\n'.encode())
    await writer.drain()
    respuesta = await reader.read()              # HTTP/1.0: lee hasta que cierre
    writer.close()
    await writer.wait_closed()
    return respuesta.split(b'\r\n\r\n', 1)[1]


async def medir(etiqueta, corrutinas):
    t0 = time.perf_counter()
    resultados = await asyncio.gather(*corrutinas)
    print(f'  {etiqueta:<42} {time.perf_counter() - t0:5.2f}s '
          f'({len(resultados)} respuestas)')


async def principal(puerto):
    url = f'http://127.0.0.1:{puerto}/'
    print(f'{N} descargas de un servidor que tarda {DEMORA}s:\n')
    await medir('urllib adentro de la corrutina (bug)',
                (bajar_mal(url) for _ in range(N)))
    await medir('urllib con asyncio.to_thread',
                (bajar_en_thread(url) for _ in range(N)))
    await medir('asyncio.open_connection',
                (bajar_async('127.0.0.1', puerto) for _ in range(N)))


def main():
    parser = argparse.ArgumentParser(description='Encontrar el bloqueo')
    parser.add_argument('--port', type=int, default=8080)
    args = parser.parse_args()

    servidor = ServidorHTTP(('127.0.0.1', args.port), HandlerLento)
    threading.Thread(target=servidor.serve_forever, daemon=True).start()
    try:
        asyncio.run(principal(args.port))
    finally:
        servidor.shutdown()
        servidor.server_close()


if __name__ == '__main__':
    main()
