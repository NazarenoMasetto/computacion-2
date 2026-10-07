#!/usr/bin/env python3
"""Ejercicio 4.3 - Singleton con metaclase.

Al hacer Clase(...) Python llama a type(Clase).__call__, o sea al __call__ de
la metaclase. Ahí interceptamos: si ya hay una instancia la devolvemos, si no
la creamos con super().__call__ (que llama a __new__ y __init__).
"""

import threading


class Singleton(type):
    """Metaclase: cada clase que la use tiene una única instancia."""

    _instancias: dict[type, object] = {}
    _lock = threading.Lock()  # para que dos hilos no creen dos instancias

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instancias:
            with cls._lock:
                if cls not in cls._instancias:
                    cls._instancias[cls] = super().__call__(*args, **kwargs)
        return cls._instancias[cls]


class Configuracion(metaclass=Singleton):
    def __init__(self, debug=False):
        self.debug = debug


class Logger(metaclass=Singleton):
    def __init__(self):
        self.mensajes = []


if __name__ == "__main__":
    c1 = Configuracion(debug=True)
    c2 = Configuracion(debug=False)  # NO crea nueva instancia ni re-ejecuta __init__
    print(c1 is c2)   # True
    print(c1.debug)   # True

    # Cada clase tiene su propia instancia única
    l1, l2 = Logger(), Logger()
    print(l1 is l2, l1 is c1)  # True False

    # Con hilos también hay una sola
    resultados = []
    hilos = [threading.Thread(target=lambda: resultados.append(Configuracion()))
             for _ in range(10)]
    for h in hilos:
        h.start()
    for h in hilos:
        h.join()
    print("Instancias distintas creadas por 10 hilos:", len({id(r) for r in resultados}))
