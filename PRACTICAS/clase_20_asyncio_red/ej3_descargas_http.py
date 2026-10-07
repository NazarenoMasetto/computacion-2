#!/usr/bin/env python3
"""Ejercicio 3 (obligatorio), partes B, C y D: descargas HTTP reales.

Mide, con httpx y un AsyncClient reutilizado:
    B. secuencial contra gather, un cliente por descarga, y requests
       metido adentro de una corrutina
    C. gather acotado con Semaphore(3)
    D. una URL inválida con gather normal y con return_exceptions=True
Con --muchas N: N descargas sin semáforo (parte C, punto 9).

Por defecto descarga de servidor_prueba.py (local), porque en el entorno
donde lo probé no había salida a internet. Con salida, usar:
    python3 ej3_descargas_http.py --url https://example.com

Uso:
    python3 servidor_prueba.py &          # en otra terminal
    python3 ej3_descargas_http.py
    python3 ej3_descargas_http.py --muchas 200 --ulimit 150
"""
import argparse
import asyncio
import resource
import time

import httpx
import requests

URL_INVALIDA = 'http://no-existe.invalid/'


async def bajar(cliente, url):
    r = await cliente.get(url)
    return url, r.status_code, len(r.content)


def bajar_con_requests(url):
    """Igual que bajar() pero con requests: sincrónico."""
    r = requests.get(url, timeout=10)
    return url, r.status_code, len(r.content)


async def cronometrar(etiqueta, corrutina):
    t0 = time.perf_counter()
    resultado = await corrutina
    print(f'  {etiqueta:<42} {time.perf_counter() - t0:6.2f}s')
    return resultado


# ---------------------------------------------------------------
# Parte B
# ---------------------------------------------------------------

async def secuencial(urls):
    async with httpx.AsyncClient(timeout=10) as cliente:
        return [await bajar(cliente, u) for u in urls]


async def concurrente(urls):
    # El cliente se crea UNA vez y se comparte: pool de conexiones keep-alive
    async with httpx.AsyncClient(timeout=10) as cliente:
        return await asyncio.gather(*(bajar(cliente, u) for u in urls))


async def secuencial_cliente_por_descarga(urls):
    """Mal: un AsyncClient nuevo por cada descarga (conexión nueva cada vez)."""
    resultados = []
    for u in urls:
        async with httpx.AsyncClient(timeout=10) as cliente:
            resultados.append(await bajar(cliente, u))
    return resultados


async def concurrente_con_requests(urls):
    """requests adentro de corrutinas: el gather no sirve de nada."""
    async def bajar_mal(url):
        return bajar_con_requests(url)       # bloquea el loop entero
    return await asyncio.gather(*(bajar_mal(u) for u in urls))


# ---------------------------------------------------------------
# Parte C
# ---------------------------------------------------------------

async def con_semaforo(urls, limite=3):
    sem = asyncio.Semaphore(limite)
    async with httpx.AsyncClient(timeout=10) as cliente:
        async def acotada(url):
            async with sem:                   # como mucho `limite` a la vez
                return await bajar(cliente, url)
        return await asyncio.gather(*(acotada(u) for u in urls))


async def muchas(url, n, limite=None):
    """n descargas a la vez; con `limite`, acotadas por un semáforo."""
    sem = asyncio.Semaphore(limite) if limite else None

    async def una(cliente):
        if sem is None:
            return await bajar(cliente, url)
        async with sem:
            return await bajar(cliente, url)

    # OJO: el AsyncClient por defecto ya limita a 100 conexiones (es un
    # semáforo escondido). Se lo sacamos para ver el problema de verdad.
    sin_limite = httpx.Limits(max_connections=None, max_keepalive_connections=None)
    async with httpx.AsyncClient(timeout=30, limits=sin_limite) as cliente:
        resultados = await asyncio.gather(*(una(cliente) for _ in range(n)),
                                          return_exceptions=True)
    errores = [r for r in resultados if isinstance(r, Exception)]
    print(f'  ok: {n - len(errores)}  errores: {len(errores)}')
    # httpx envuelve el error real; la causa de fondo está en __cause__/__context__
    causas = set()
    for e in errores:
        fondo = e
        while fondo.__cause__ or fondo.__context__:
            fondo = fondo.__cause__ or fondo.__context__
        causas.add(f'{type(e).__name__}: {e}  <- causa: {type(fondo).__name__}: {fondo}')
    for c in causas:
        print(f'    {c}')


# ---------------------------------------------------------------
# Parte D
# ---------------------------------------------------------------

async def con_fallo(urls, return_exceptions):
    async with httpx.AsyncClient(timeout=10) as cliente:
        tareas = [asyncio.ensure_future(bajar(cliente, u)) for u in urls]
        try:
            resultados = await asyncio.gather(*tareas, return_exceptions=return_exceptions)
        except Exception as e:
            print(f'  gather lanzó {type(e).__name__}: {e}')
            print('  los resultados de las que anduvieron se pierden (no hay lista)')
            await asyncio.sleep(1.5)          # ¿las demás siguieron corriendo?
            terminadas = sum(1 for t in tareas if t.done() and not t.exception())
            print(f'  igual, {terminadas} tareas terminaron bien en segundo plano '
                  '(gather NO las cancela)')
            return
        for r in resultados:
            if isinstance(r, Exception):
                print(f'  -> excepción como valor: {type(r).__name__}: {r}')
            else:
                print(f'  -> {r[1]} {r[2]} bytes')


async def main(args):
    url = args.url
    if args.ulimit:
        _, duro = resource.getrlimit(resource.RLIMIT_NOFILE)
        resource.setrlimit(resource.RLIMIT_NOFILE, (args.ulimit, duro))
        print(f'ulimit -n bajado a {args.ulimit} para este proceso')

    if args.muchas:
        print(f'\n{args.muchas} descargas sin semáforo:')
        await muchas(url, args.muchas)
        print(f'\n{args.muchas} descargas con Semaphore(50):')
        await muchas(url, args.muchas, limite=50)
        return

    urls = [url] * args.n
    print(f'{args.n} descargas de {url}\n')
    print('Parte B')
    r = await cronometrar('secuencial (un AsyncClient compartido)', secuencial(urls))
    print(f'    ejemplo: {r[0]}')
    await cronometrar('secuencial (un AsyncClient por descarga)',
                      secuencial_cliente_por_descarga(urls))
    await cronometrar('gather (un AsyncClient compartido)', concurrente(urls))
    await cronometrar('gather con requests adentro', concurrente_con_requests(urls))

    print('\nParte C')
    await cronometrar('gather con Semaphore(3)', con_semaforo(urls, 3))

    print('\nParte D: se agrega', URL_INVALIDA)
    urls_con_fallo = urls[:4] + [URL_INVALIDA]
    print(' gather normal:')
    await con_fallo(urls_con_fallo, return_exceptions=False)
    print(' gather(..., return_exceptions=True):')
    await con_fallo(urls_con_fallo, return_exceptions=True)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument('--url', default='http://127.0.0.1:8085/')
    p.add_argument('-n', type=int, default=10, help='cantidad de descargas')
    p.add_argument('--muchas', type=int, default=0, help='punto 9: N descargas sin semáforo')
    p.add_argument('--ulimit', type=int, default=0, help='bajar ulimit -n de este proceso')
    asyncio.run(main(p.parse_args()))
