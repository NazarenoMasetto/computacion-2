#!/usr/bin/env python3
"""Ejercicio 2.2: las cuatro formas de leer de un StreamReader.

Para cada forma se abre una conexión nueva, el cliente manda
'hola\\nmundo\\n' y el servidor hace UNA lectura y muestra qué obtuvo.
Al final, los dos casos borde: readexactly(100) con menos datos, y
read() cuando el cliente ya cerró.

Uso:
    python3 ej2_lecturas.py [puerto]      # por defecto 8080
"""
import asyncio
import os
import sys

PUERTO = int(sys.argv[1]) if len(sys.argv) > 1 else int(os.environ.get('PUERTO', 8080))
MENSAJE = b'hola\nmundo\n'

FORMAS = [
    ('read(100)', lambda r: r.read(100)),
    ('readline()', lambda r: r.readline()),
    ('readexactly(4)', lambda r: r.readexactly(4)),
    ("readuntil(b'\\n')", lambda r: r.readuntil(b'\n')),
]


async def probar(etiqueta, leer, mensaje=MENSAJE):
    """Levanta un servidor que hace una sola lectura con `leer`."""
    resultado = asyncio.get_running_loop().create_future()

    async def manejar(reader, writer):
        try:
            primero = await leer(reader)
            resto = await reader.read()        # lo que quedó sin leer
            resultado.set_result(f'{primero!r:<22} (quedó en el buffer: {resto!r})')
        except Exception as e:
            resultado.set_result(f'{type(e).__name__}: {e}')
        writer.close()

    srv = await asyncio.start_server(manejar, '127.0.0.1', PUERTO)
    async with srv:
        _, w = await asyncio.open_connection('127.0.0.1', PUERTO)
        w.write(mensaje)
        await w.drain()
        w.close()                              # EOF para el servidor
        print(f'  {etiqueta:<22} -> {await resultado}')


async def main():
    print(f"Cliente manda {MENSAJE!r} y cierra:\n")
    for etiqueta, leer in FORMAS:
        await probar(etiqueta, leer)

    print('\nCasos borde:\n')
    await probar('readexactly(100)', lambda r: r.readexactly(100))

    # read() cuando el cliente cerró sin mandar nada: b'' (como recv en la clase 13)
    await probar('read() tras cierre', lambda r: r.read(100), mensaje=b'')


if __name__ == '__main__':
    asyncio.run(main())
