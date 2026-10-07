#!/usr/bin/env python3
"""Ejercicio adicional: proxy TCP asíncrono.

Acepta conexiones y reenvía todo a otro host, en los dos sentidos a la
vez. Por cada conexión hay dos tareas (cliente -> destino y destino ->
cliente); cuando una termina, se cancela la otra.

Detalle: si una dirección termina por EOF "limpio" (el otro hizo
shutdown de escritura, como `nc -q`), se propaga el EOF con write_eof()
y se le da a la otra dirección un rato (ESPERA) para que termine de
mandar la respuesta antes de cancelarla. Si termina por error, se
cancela la otra enseguida.

Uso:
    python3 proxy_async.py DESTINO_HOST DESTINO_PUERTO [PUERTO_LOCAL]
    python3 proxy_async.py localhost 8080 9090     # por defecto escucha en 9090

Ejemplo: con eco_async.py en 8080, `nc localhost 9090` habla con el eco.
"""
import asyncio
import os
import sys

ESPERA = 10         # segundos de gracia después de un EOF limpio


async def bombear(reader, writer, sentido):
    """Copia todo lo que llega de reader hacia writer hasta EOF."""
    total = 0
    while datos := await reader.read(64 * 1024):
        writer.write(datos)
        await writer.drain()                 # si el otro lado es lento, frenamos
        total += len(datos)
    if writer.can_write_eof():
        writer.write_eof()                   # propagar el "ya no mando más"
    return sentido, total


async def manejar(cliente_r, cliente_w, destino_host, destino_puerto):
    origen = cliente_w.get_extra_info('peername')
    try:
        destino_r, destino_w = await asyncio.open_connection(destino_host, destino_puerto)
    except OSError as e:
        print(f'{origen}: no pude conectar con el destino ({e})')
        cliente_w.close()
        return
    print(f'+ {origen} <-> {destino_host}:{destino_puerto}')

    ida = asyncio.create_task(bombear(cliente_r, destino_w, 'cliente->destino'))
    vuelta = asyncio.create_task(bombear(destino_r, cliente_w, 'destino->cliente'))

    # Esperar a que termine CUALQUIERA de las dos y cancelar la otra
    hechas, pendientes = await asyncio.wait({ida, vuelta},
                                            return_when=asyncio.FIRST_COMPLETED)
    if pendientes and not any(t.exception() for t in hechas):
        # EOF limpio: darle tiempo a la otra dirección a terminar sola
        mas, pendientes = await asyncio.wait(pendientes, timeout=ESPERA)
        hechas |= mas
    for tarea in pendientes:
        tarea.cancel()
    await asyncio.gather(*pendientes, return_exceptions=True)

    for tarea in hechas:
        if tarea.exception():
            print(f'  {origen}: error {tarea.exception()!r}')
        else:
            sentido, total = tarea.result()
            print(f'  {origen}: terminó {sentido} ({total} bytes)')
    for w in (cliente_w, destino_w):
        w.close()
    print(f'- {origen}')


async def main(destino_host, destino_puerto, puerto_local):
    async def handler(r, w):
        await manejar(r, w, destino_host, destino_puerto)

    srv = await asyncio.start_server(handler, '0.0.0.0', puerto_local)
    print(f'Proxy en 0.0.0.0:{puerto_local} -> {destino_host}:{destino_puerto}')
    async with srv:
        await srv.serve_forever()


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    local = int(sys.argv[3]) if len(sys.argv) > 3 else int(os.environ.get('PUERTO', 9090))
    try:
        asyncio.run(main(sys.argv[1], int(sys.argv[2]), local))
    except KeyboardInterrupt:
        pass
