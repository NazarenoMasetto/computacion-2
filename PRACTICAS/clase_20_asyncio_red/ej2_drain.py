#!/usr/bin/env python3
"""Ejercicio 2.3: para qué sirve drain().

Un servidor eco y un cliente que manda 100 MB SIN leer nunca la respuesta.
Se mide la memoria (RSS) del servidor con y sin `await writer.drain()`.

    - Con drain: cuando el buffer de salida pasa el límite (64 KB por
      defecto), drain() suspende al handler hasta que el cliente lea. El
      handler deja de leer, el buffer del kernel se llena y TCP frena al
      cliente (backpressure). La memoria queda chica.
    - Sin drain: write() acumula todo en el buffer del transporte y la
      memoria crece hasta los ~100 MB que mandó el cliente.

Uso:
    python3 ej2_drain.py                       # corre los dos casos y compara
    python3 ej2_drain.py servidor 30110 [--sin-drain]
    python3 ej2_drain.py cliente 30110 [MB]
"""
import asyncio
import os
import socket
import subprocess
import sys
import time

PUERTO = int(os.environ.get('PUERTO', 8080))
MB = 1024 * 1024


def rss_mb():
    """Memoria residente del proceso actual, leída de /proc (Linux)."""
    with open('/proc/self/status') as f:
        for linea in f:
            if linea.startswith('VmRSS:'):
                return int(linea.split()[1]) / 1024
    return 0.0


async def servidor(puerto, con_drain):
    pico = rss_mb()

    async def manejar(reader, writer):
        nonlocal pico
        recibidos = 0
        buffer_max = 0
        try:
            while datos := await reader.read(64 * 1024):
                recibidos += len(datos)
                writer.write(datos)              # eco: el cliente nunca lo lee
                if con_drain:
                    await writer.drain()         # espera si el buffer está lleno
                pico = max(pico, rss_mb())
                buffer_max = max(buffer_max, writer.transport.get_write_buffer_size())
        except (ConnectionResetError, BrokenPipeError):
            pass
        finally:
            print(f'servidor: recibidos {recibidos / MB:6.1f} MB | '
                  f'buffer de salida máx {buffer_max / MB:6.1f} MB | '
                  f'RSS pico {pico:6.1f} MB', flush=True)
            writer.close()

    srv = await asyncio.start_server(manejar, '127.0.0.1', puerto)
    print(f'servidor listo (drain={"sí" if con_drain else "no"}, '
          f'RSS inicial {rss_mb():.1f} MB)', flush=True)
    async with srv:
        await srv.serve_forever()


def cliente(puerto, megas):
    """Cliente bloqueante común: manda y manda, nunca hace recv()."""
    s = socket.create_connection(('127.0.0.1', puerto))
    s.settimeout(3)                     # si el servidor nos frena 3 s, cortamos
    pedazo = b'x' * (64 * 1024)
    enviados = 0
    try:
        while enviados < megas * MB:
            s.sendall(pedazo)
            enviados += len(pedazo)
    except socket.timeout:
        print(f'cliente: frenado por TCP después de {enviados / MB:.1f} MB '
              '(el servidor dejó de leer)')
    else:
        print(f'cliente: mandó los {enviados / MB:.0f} MB completos')
    time.sleep(0.5)                     # darle tiempo al servidor a procesar
    s.close()


def comparar():
    """Levanta el servidor en un subproceso para cada caso y lo mide."""
    for i, extra in enumerate(([], ['--sin-drain'])):
        puerto = PUERTO + i
        srv = subprocess.Popen([sys.executable, __file__, 'servidor', str(puerto), *extra],
                               stdout=subprocess.PIPE, text=True)
        print(srv.stdout.readline().strip())
        cliente(puerto, 100)
        time.sleep(1)
        srv.terminate()
        print(srv.stdout.read().strip(), '\n')
        srv.wait()


if __name__ == '__main__':
    if len(sys.argv) > 2 and sys.argv[1] == 'servidor':
        try:
            asyncio.run(servidor(int(sys.argv[2]), '--sin-drain' not in sys.argv))
        except KeyboardInterrupt:
            pass
    elif len(sys.argv) > 2 and sys.argv[1] == 'cliente':
        cliente(int(sys.argv[2]), int(sys.argv[3]) if len(sys.argv) > 3 else 100)
    else:
        comparar()
