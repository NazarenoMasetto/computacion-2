#!/usr/bin/env python3
"""Ejercicio 3: el puente entre generadores y async/await.

Verifica que una corrutina tiene .send() y devuelve por StopIteration,
que await funciona sobre un generador con @types.coroutine, y muestra la
traducción de la sintaxis vieja (yield from) a la moderna (await).

Uso:
    python3 ej3_puente.py
"""
import asyncio
import types


async def f():
    return 99


# --- 3.5: la traducción ---------------------------------------
# Versión vieja (ya no existe @asyncio.coroutine desde Python 3.11):
#
#     @asyncio.coroutine
#     def buscar(id):
#         conn = yield from abrir()
#         datos = yield from leer(conn, id)
#         return datos
#
# Versión moderna:

async def abrir():
    await asyncio.sleep(0.01)             # simula abrir una conexión
    return 'conexion'


async def leer(conn, id):
    await asyncio.sleep(0.01)             # simula leer de esa conexión
    return f'datos del id {id} por {conn}'


async def buscar(id):
    conn = await abrir()
    datos = await leer(conn, id)
    return datos


@types.coroutine
def generador_puente():
    recibido = yield 'pausa'
    return recibido


async def usa_puente():
    return await generador_puente()


def main():
    print('=== 3.1 / 3.2 una corrutina tiene send() ===')
    c = f()
    print('  type(f()):', type(c).__name__, '-> el cuerpo todavía NO corrió')
    print('  hasattr(c, "send"):', hasattr(c, 'send'))
    try:
        c.send(None)
    except StopIteration as e:
        print('  c.send(None) -> StopIteration.value =', e.value)

    print('\n=== 3.4 await sobre un generador con @types.coroutine ===')
    co = usa_puente()
    print('  co.send(None) ->', repr(co.send(None)), '(subió el yield del generador)')
    try:
        co.send('hola')
    except StopIteration as e:
        print('  co.send("hola") -> StopIteration.value =', repr(e.value))

    print('\n=== 3.5 la traducción a async/await ===')
    print('  ', asyncio.run(buscar(7)))
    print('   ¿existe asyncio.coroutine?', hasattr(asyncio, 'coroutine'))


if __name__ == '__main__':
    main()
