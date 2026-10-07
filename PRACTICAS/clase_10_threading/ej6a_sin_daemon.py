#!/usr/bin/env python3
"""Ejercicio 6.1: hilo NO daemon con loop infinito. El programa NO termina solo (cortar con Ctrl+C)."""
import threading
import time


def loop_infinito(label):
    while True:
        print(f"[{label}] trabajando...", flush=True)
        time.sleep(1)


if __name__ == "__main__":
    h = threading.Thread(target=loop_infinito, args=("no-daemon",))
    h.start()
    time.sleep(3)
    print("Main terminó pero el programa sigue vivo (Ctrl+C para cortar)", flush=True)
