#!/usr/bin/env python3
"""Ejercicio adicional: el chat de la clase 17, reescrito con asyncio.

Una corrutina por cliente; el conjunto de writers conectados es el
estado compartido. Para difundir se escribe en todos los demás.

Uso:
    python3 chat_async.py [puerto]      # por defecto 8080 (o PUERTO=...)
    nc localhost 8080                   # desde varias terminales
"""
import asyncio
import os
import sys

PUERTO = int(sys.argv[1]) if len(sys.argv) > 1 else int(os.environ.get('PUERTO', 8080))

clientes = {}           # writer -> apodo. Sin lock: un solo hilo


async def difundir(mensaje: bytes, excepto=None):
    """Manda el mensaje a todos menos a `excepto`."""
    for writer in list(clientes):          # copia: puede cambiar mientras esperamos
        if writer is excepto:
            continue
        writer.write(mensaje)
    # drain después de escribir a todos. Si un cliente está lento, esto
    # espera por él; para un chat de clase alcanza (ver respuestas).
    for writer in list(clientes):
        if writer is not excepto:
            try:
                await writer.drain()
            except ConnectionError:
                pass


async def manejar(reader, writer):
    host, puerto = writer.get_extra_info('peername')[:2]
    apodo = f'{host}:{puerto}'
    clientes[writer] = apodo
    print(f'+ {apodo}  ({len(clientes)} conectados)')
    writer.write(b'Bienvenido al chat. Escribi y presiona Enter.\n')
    await difundir(f'* se conecto {apodo}\n'.encode(), excepto=writer)
    try:
        while linea := await reader.readline():
            texto = linea.decode('utf-8', errors='replace').rstrip('\r\n')
            if texto:
                print(f'  <{apodo}> {texto}')
                await difundir(f'<{apodo}> {texto}\n'.encode(), excepto=writer)
    except ConnectionError:
        pass
    finally:
        del clientes[writer]
        print(f'- {apodo}  ({len(clientes)} conectados)')
        writer.close()
        await difundir(f'* se fue {apodo}\n'.encode())


async def main():
    srv = await asyncio.start_server(manejar, '0.0.0.0', PUERTO)
    print(f'Chat escuchando en 0.0.0.0:{PUERTO} (asyncio)')
    print('Conectate con: nc localhost', PUERTO)
    async with srv:
        await srv.serve_forever()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('\nChat detenido')
