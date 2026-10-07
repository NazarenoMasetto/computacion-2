#!/usr/bin/env python3
"""Ejercicio adicional: el servidor de comandos de la clase 16, con asyncio.

Mismos comandos: TIME, ECHO <texto>, QUIEN, CONTADOR, AYUDA, QUIT.
El estado compartido (conexiones totales y clientes activos) vive en
variables del módulo y NO tiene Lock: todas las corrutinas corren en
el mismo hilo y ninguna sección crítica tiene un await en el medio.

Uso:
    python3 comandos_async.py [puerto]   # por defecto 8080 (o PUERTO=...)
    nc localhost 8080
"""
import asyncio
import os
import sys
import time

PUERTO = int(sys.argv[1]) if len(sys.argv) > 1 else int(os.environ.get('PUERTO', 8080))

conexiones = 0          # total desde el arranque
activos = set()         # (host, puerto) conectados ahora


async def manejar(reader, writer):
    global conexiones
    direccion = writer.get_extra_info('peername')[:2]
    # "setup": sin await en el medio, así que es atómico
    conexiones += 1
    activos.add(direccion)

    def responder(texto):
        writer.write((texto + '\n').encode())

    try:
        responder('Servidor de comandos. Escribí AYUDA.')
        while linea := await reader.readline():       # framing por líneas
            partes = linea.decode('utf-8', 'replace').strip().split(maxsplit=1)
            if not partes:
                continue
            cmd, resto = partes[0].upper(), (partes[1] if len(partes) > 1 else '')

            if cmd == 'TIME':
                responder(time.strftime('%Y-%m-%d %H:%M:%S'))
            elif cmd == 'ECHO':
                responder(resto)
            elif cmd == 'QUIEN':
                lista = sorted(f'{h}:{p}' for h, p in activos)   # sin lock
                responder(f'{len(lista)} conectados: ' + ', '.join(lista))
            elif cmd == 'CONTADOR':
                responder(f'Conexiones totales desde el arranque: {conexiones}')
            elif cmd == 'AYUDA':
                responder('TIME | ECHO <texto> | QUIEN | CONTADOR | QUIT')
            elif cmd == 'QUIT':
                responder('Chau')
                break
            else:
                responder(f'Comando desconocido: {cmd}')
            await writer.drain()
    except ConnectionError:
        pass
    except Exception as e:
        # como handle_error() de socketserver: el servidor no se cae
        print(f'Error atendiendo a {direccion}: {e!r}')
    finally:
        # "finish": también sin await antes de tocar el estado
        activos.discard(direccion)
        writer.close()


async def main():
    srv = await asyncio.start_server(manejar, '0.0.0.0', PUERTO)
    print(f'Escuchando en 0.0.0.0:{PUERTO}')
    print('Probá: nc localhost', PUERTO)
    async with srv:
        await srv.serve_forever()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('\nServidor detenido')
