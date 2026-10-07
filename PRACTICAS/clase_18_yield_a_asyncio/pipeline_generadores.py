#!/usr/bin/env python3
"""Adicional: pipeline de corrutinas-generador con send().

Tres etapas encadenadas, cada una empuja (send) lo que produce a la
siguiente: lector -> filtro -> contador. Es el patrón "coroutine pipeline"
de David Beazley, previo a asyncio.

Uso:
    python3 pipeline_generadores.py [archivo] [--patron texto]
    (sin archivo, lee este mismo script)
"""
import argparse
import functools


def arrancar(func):
    """Decorador: crea el generador y lo avanza hasta el primer yield,
    así ya está listo para recibir send()."""
    @functools.wraps(func)
    def envoltura(*args, **kwargs):
        g = func(*args, **kwargs)
        next(g)
        return g
    return envoltura


def leer_lineas(ruta, destino):
    """Productor: lee el archivo y empuja cada línea al destino."""
    with open(ruta, encoding='utf-8') as f:
        for linea in f:
            destino.send(linea.rstrip('\n'))
    destino.close()                  # avisa el fin hacia abajo


@arrancar
def filtrar(patron, destino):
    """Etapa intermedia: deja pasar solo las líneas que contienen el patrón."""
    try:
        while True:
            linea = yield
            if patron in linea:
                destino.send(linea)
    except GeneratorExit:
        destino.close()              # propaga el cierre


@arrancar
def contar(resultado):
    """Sumidero: cuenta y muestra lo que le llega."""
    n = 0
    try:
        while True:
            linea = yield
            n += 1
            print(f'  {n:3}: {linea}')
    except GeneratorExit:
        resultado['total'] = n


def main():
    parser = argparse.ArgumentParser(description='Pipeline de generadores')
    parser.add_argument('archivo', nargs='?', default=__file__)
    parser.add_argument('--patron', default='yield')
    args = parser.parse_args()

    resultado = {}
    # Se arma de atrás para adelante: cada etapa recibe a la siguiente
    leer_lineas(args.archivo, filtrar(args.patron, contar(resultado)))
    print(f'Líneas con {args.patron!r}: {resultado["total"]}')


if __name__ == '__main__':
    main()
