#!/usr/bin/env python3
"""
Ejercicio 5 (obligatorio): Readers-Writers Lock.

Reglas:
- Múltiples lectores pueden leer simultáneamente
- Solo un escritor puede escribir a la vez
- Mientras hay escritor, no pueden haber lectores
- Mientras hay lectores, no pueden haber escritores

Mejora sobre la especificación: se cuentan los escritores ESPERANDO y los
lectores nuevos ceden el paso si hay alguno. Así un flujo continuo de
lectores no deja con hambre (starvation) a los escritores.
"""
import random
import threading
import time


class ReadWriteLock:
    def __init__(self):
        self.readers = 0            # lectores leyendo ahora
        self.writers = 0            # escritores escribiendo ahora (0 o 1)
        self.writers_waiting = 0    # escritores esperando turno
        self.lock = threading.Lock()
        # Dos Condition sobre el MISMO lock: dos "salas de espera" distintas
        self.can_read = threading.Condition(self.lock)
        self.can_write = threading.Condition(self.lock)

    def acquire_read(self):
        """Adquirir lock para lectura."""
        with self.lock:
            # Preferencia a escritores: si hay uno esperando, no me cuelo
            while self.writers > 0 or self.writers_waiting > 0:
                self.can_read.wait()
            self.readers += 1

    def release_read(self):
        """Liberar lock de lectura."""
        with self.lock:
            self.readers -= 1
            if self.readers == 0:
                self.can_write.notify()

    def acquire_write(self):
        """Adquirir lock para escritura."""
        with self.lock:
            self.writers_waiting += 1
            while self.readers > 0 or self.writers > 0:
                self.can_write.wait()
            self.writers_waiting -= 1
            self.writers += 1

    def release_write(self):
        """Liberar lock de escritura."""
        with self.lock:
            self.writers -= 1
            if self.writers_waiting > 0:
                self.can_write.notify()       # sigue otro escritor
            else:
                self.can_read.notify_all()    # entran todos los lectores juntos


# Context managers para uso más simple
class ReadLock:
    def __init__(self, rwlock):
        self.rwlock = rwlock

    def __enter__(self):
        self.rwlock.acquire_read()

    def __exit__(self, *args):
        self.rwlock.release_read()


class WriteLock:
    def __init__(self, rwlock):
        self.rwlock = rwlock

    def __enter__(self):
        self.rwlock.acquire_write()

    def __exit__(self, *args):
        self.rwlock.release_write()


# Test
rwlock = ReadWriteLock()
datos = {"valor": 0, "lecturas": 0, "escrituras": 0}

# Instrumentación para verificar las reglas (protegida por su propio lock)
control = threading.Lock()
estado = {"leyendo": 0, "escribiendo": 0, "max_lectores": 0, "violaciones": 0}


def entrar(tipo):
    with control:
        estado[tipo] += 1
        if estado["escribiendo"] > 1 or (estado["escribiendo"] and estado["leyendo"]):
            estado["violaciones"] += 1
        estado["max_lectores"] = max(estado["max_lectores"], estado["leyendo"])


def salir(tipo):
    with control:
        estado[tipo] -= 1


def lector(id):
    for _ in range(5):
        with ReadLock(rwlock):
            entrar("leyendo")
            valor = datos["valor"]
            # Varios lectores pueden estar acá a la vez: protegemos el contador
            with control:
                datos["lecturas"] += 1
            print(f"[Lector {id}] Leyó valor={valor}")
            time.sleep(random.uniform(0.05, 0.15))
            salir("leyendo")
        time.sleep(random.uniform(0.1, 0.2))


def escritor(id):
    for i in range(3):
        with WriteLock(rwlock):
            entrar("escribiendo")
            datos["valor"] = id * 100 + i
            datos["escrituras"] += 1
            print(f"[Escritor {id}] Escribió valor={datos['valor']}")
            time.sleep(random.uniform(0.1, 0.2))
            salir("escribiendo")
        time.sleep(random.uniform(0.2, 0.4))


if __name__ == "__main__":
    threads = []
    for i in range(5):
        threads.append(threading.Thread(target=lector, args=(i,)))
    for i in range(2):
        threads.append(threading.Thread(target=escritor, args=(i,)))

    random.shuffle(threads)  # Mezclar orden de inicio

    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=30)
        if t.is_alive():
            print("¡Algún thread no terminó: posible deadlock!")

    print("\nEstadísticas finales:")
    print(f"  Valor final: {datos['valor']}")
    print(f"  Total lecturas: {datos['lecturas']} (esperadas 25)")
    print(f"  Total escrituras: {datos['escrituras']} (esperadas 6)")
    print("\nVerificación de reglas:")
    print(f"  Máximo de lectores simultáneos: {estado['max_lectores']} (>1 = lectura concurrente)")
    print(f"  Violaciones de exclusión: {estado['violaciones']} (tiene que ser 0)")
