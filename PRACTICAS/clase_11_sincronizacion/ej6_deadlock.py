#!/usr/bin/env python3
"""Ejercicio 6: demostración y prevención de deadlock.

Cambio respecto de la consigna: los threads de la versión con deadlock se
crean como daemon. Si no, después de detectar el deadlock el intérprete se
queda esperando para siempre a esos dos threads trabados y el programa
nunca termina.
"""
import threading
import time


def demostrar_deadlock():
    """Dos threads toman los locks en orden opuesto -> espera circular."""
    lock_a = threading.Lock()
    lock_b = threading.Lock()

    def thread_1():
        with lock_a:
            print("Thread 1: tiene A")
            time.sleep(0.1)          # da tiempo a que el otro tome B
            with lock_b:
                print("Thread 1: tiene A y B")

    def thread_2():
        with lock_b:
            print("Thread 2: tiene B")
            time.sleep(0.1)
            with lock_a:
                print("Thread 2: tiene B y A")

    t1 = threading.Thread(target=thread_1, daemon=True)
    t2 = threading.Thread(target=thread_2, daemon=True)

    t1.start()
    t2.start()

    # Timeout para detectar deadlock
    t1.join(timeout=2)
    t2.join(timeout=2)

    if t1.is_alive() or t2.is_alive():
        print("¡DEADLOCK DETECTADO!")
        return False
    return True


def version_corregida():
    """Ambos threads toman los locks en el mismo orden: A y después B."""
    lock_a = threading.Lock()
    lock_b = threading.Lock()

    def thread_ordenado(nombre):
        with lock_a:  # Siempre A primero
            print(f"{nombre}: tiene A")
            with lock_b:  # Luego B
                print(f"{nombre}: tiene A y B")
                time.sleep(0.1)

    t1 = threading.Thread(target=thread_ordenado, args=("Thread 1",))
    t2 = threading.Thread(target=thread_ordenado, args=("Thread 2",))

    t1.start()
    t2.start()
    t1.join()
    t2.join()

    print("¡Completado sin deadlock!")


if __name__ == "__main__":
    print("=== Versión con deadlock ===")
    demostrar_deadlock()

    print("\n=== Versión corregida ===")
    version_corregida()
