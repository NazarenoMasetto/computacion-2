#!/usr/bin/env python3
"""Ejercicio 1: generadores que reciben (send), estado que sobrevive y
StopIteration con el resultado.

Uso:
    python3 ej1_generadores.py
"""


def acumulador():
    total = 0
    while True:
        n = yield total
        total += n


def contador():
    n = 0
    while True:
        print(f'  voy por {n}')
        yield
        n += 1


def tarea():
    yield 'trabajando'
    return 'resultado final'


def main():
    print('=== 1.1 send() ===')
    a = acumulador()
    try:
        a.send(10)                       # sin arrancar antes
    except TypeError as e:
        print(f'  a.send(10) sin next(): TypeError: {e}')
    print(f'  next(a) -> {next(a)}       (llega hasta el primer yield con total=0)')
    for n in (10, 5, 7):
        print(f'  a.send({n}) -> {a.send(n)}')

    print('\n=== 1.2 El estado sobrevive ===')
    c1, c2 = contador(), contador()
    for nombre, g in (('c1', c1), ('c1', c1), ('c2', c2), ('c1', c1), ('c2', c2)):
        print(f' next({nombre}):')
        next(g)
    # El n vive en el frame del generador, que sigue vivo entre llamadas
    print(f'  frame de c1: n = {c1.gi_frame.f_locals["n"]}, '
          f'frame de c2: n = {c2.gi_frame.f_locals["n"]}')

    print('\n=== 1.3 StopIteration lleva el resultado ===')
    t = tarea()
    print(f'  next(t) -> {next(t)!r}')
    try:
        next(t)
    except StopIteration as e:
        print(f'  StopIteration.value = {e.value!r}')


if __name__ == '__main__':
    main()
