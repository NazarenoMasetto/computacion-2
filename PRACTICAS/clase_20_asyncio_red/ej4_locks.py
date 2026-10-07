#!/usr/bin/env python3
"""Ejercicio 4: locks en asyncio, cuándo no hacen falta y cuándo sí.

    4.1  contador += 1 con 1000 corrutinas y con 1000 threads
    4.2  transferencias con un await en el medio: race condition,
         y el arreglo con asyncio.Lock

Uso:
    python3 ej4_locks.py
"""
import asyncio
import threading
import time

# ---------------------------------------------------------------
# 4.1 Cuándo no hacen falta
# ---------------------------------------------------------------

contador = 0


async def sumar():
    global contador
    contador += 1            # sin await en el medio: nadie puede interrumpir


async def contador_corrutinas(n=1000):
    global contador
    contador = 0
    await asyncio.gather(*(sumar() for _ in range(n)))
    return contador


def contador_threads(n_threads=1000, vueltas=1, pausa=False):
    """Lo mismo con threads (clase 11).

    Con pausa=True se mete un time.sleep(0) entre leer y escribir: suelta
    el GIL y fuerza el cambio de thread justo en la sección crítica (el
    equivalente del await asyncio.sleep(0) de la parte 4.2).
    """
    global contador
    contador = 0

    def sumar_thread():
        global contador
        for _ in range(vueltas):
            valor = contador     # leer...
            if pausa:
                time.sleep(0)    # ...cambio de thread acá...
            contador = valor + 1 # ...escribir

    hilos = [threading.Thread(target=sumar_thread) for _ in range(n_threads)]
    for h in hilos:
        h.start()
    for h in hilos:
        h.join()
    return contador


# ---------------------------------------------------------------
# 4.2 Cuándo sí
# ---------------------------------------------------------------

cuentas = {}


async def transferir(origen, destino, monto):
    saldo = cuentas[origen]
    await asyncio.sleep(0)            # un punto de suspensión en el medio
    cuentas[origen] = saldo - monto
    cuentas[destino] = cuentas[destino] + monto


async def transferir_con_lock(lock, origen, destino, monto):
    async with lock:                  # async with: adquirir puede tener que esperar
        saldo = cuentas[origen]
        await asyncio.sleep(0)
        cuentas[origen] = saldo - monto
        cuentas[destino] = cuentas[destino] + monto


async def probar_transferencias(con_lock, n=100, monto=10):
    cuentas.clear()
    cuentas.update({'A': 1000, 'B': 0})
    if con_lock:
        lock = asyncio.Lock()
        await asyncio.gather(*(transferir_con_lock(lock, 'A', 'B', monto) for _ in range(n)))
    else:
        await asyncio.gather(*(transferir('A', 'B', monto) for _ in range(n)))
    return dict(cuentas)


async def main():
    print('4.1 contador += 1')
    print(f'  1000 corrutinas:                  {await contador_corrutinas()}  (esperado 1000)')
    print(f'  1000 threads:                     {contador_threads(1000)}  (esperado 1000)')
    print(f'  8 threads x 100000:               {contador_threads(8, 100_000)}  (esperado 800000)')
    print(f'  1000 threads con sleep(0) en el medio: {contador_threads(1000, pausa=True)}  (esperado 1000)')

    print('\n4.2 100 transferencias de 10 desde A (saldo 1000) hacia B')
    sin = await probar_transferencias(con_lock=False)
    con = await probar_transferencias(con_lock=True)
    print(f'  sin lock: {sin}  -> total {sum(sin.values())}  (esperado A=0, B=1000)')
    print(f'  con lock: {con}  -> total {sum(con.values())}')


if __name__ == '__main__':
    asyncio.run(main())
