#!/usr/bin/env python3
"""Ejercicio 6.2: el mismo loop pero en un hilo daemon: muere cuando termina el principal."""
import threading
import time


def loop_infinito(label):
    while True:
        print(f"[{label}] trabajando...", flush=True)
        time.sleep(1)


if __name__ == "__main__":
    h = threading.Thread(target=loop_infinito, args=("daemon",), daemon=True)
    h.start()
    time.sleep(3)
    print("Main terminó: el daemon muere automáticamente")
