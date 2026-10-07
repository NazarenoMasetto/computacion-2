#!/usr/bin/env python3
"""
Adicional: chat multi-hilo. Varios "usuarios" (threads) mandan mensajes a una
queue.Queue central y un thread "display" los muestra a medida que llegan.
"""
import queue
import random
import threading
import time

USUARIOS = ["ana", "beto", "carla", "dani"]
MENSAJES_POR_USUARIO = 4
FRASES = ["hola!", "¿cómo va?", "todo bien", "jaja", "me voy a comer", "nos vemos", "¿alguien hizo el TP?"]


def usuario(nombre, cola):
    """Manda mensajes con pausas aleatorias."""
    for _ in range(MENSAJES_POR_USUARIO):
        time.sleep(random.uniform(0.05, 0.4))
        cola.put((time.strftime("%H:%M:%S"), nombre, random.choice(FRASES)))
    cola.put((time.strftime("%H:%M:%S"), nombre, "<se desconectó>"))


def display(cola, cantidad_usuarios):
    """Muestra mensajes hasta que todos los usuarios se desconecten."""
    desconectados = 0
    total = 0
    while desconectados < cantidad_usuarios:
        hora, nombre, texto = cola.get()  # bloquea hasta que llegue algo
        print(f"[{hora}] {nombre:>6}: {texto}")
        if texto == "<se desconectó>":
            desconectados += 1
        else:
            total += 1
    print(f"\n-- chat cerrado, {total} mensajes --")


if __name__ == "__main__":
    cola = queue.Queue()
    hilo_display = threading.Thread(target=display, args=(cola, len(USUARIOS)), name="display")
    hilo_display.start()

    hilos = [threading.Thread(target=usuario, args=(n, cola), name=n) for n in USUARIOS]
    for h in hilos:
        h.start()
    for h in hilos:
        h.join()
    hilo_display.join()
