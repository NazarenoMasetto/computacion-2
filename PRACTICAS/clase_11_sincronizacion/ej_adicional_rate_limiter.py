#!/usr/bin/env python3
"""Ejercicio adicional: rate limiter thread-safe (máximo N operaciones por segundo).

Usa una ventana deslizante: guarda los instantes de las últimas operaciones
en un deque. Si en el último segundo ya hubo N, el thread espera (con una
Condition) hasta que la más vieja salga de la ventana.

Uso:
    python3 ej_adicional_rate_limiter.py [N] [threads] [ops_por_thread]
"""
import collections
import sys
import threading
import time


class RateLimiter:
    def __init__(self, max_ops, periodo=1.0):
        self.max_ops = max_ops
        self.periodo = periodo
        self.marcas = collections.deque()   # instantes de las operaciones recientes
        self.cond = threading.Condition()

    def _limpiar(self, ahora):
        """Saca de la ventana las marcas más viejas que `periodo`."""
        while self.marcas and ahora - self.marcas[0] >= self.periodo:
            self.marcas.popleft()

    def acquire(self):
        """Bloquea hasta que haya lugar en la ventana y registra la operación."""
        with self.cond:
            while True:
                ahora = time.monotonic()
                self._limpiar(ahora)
                if len(self.marcas) < self.max_ops:
                    self.marcas.append(ahora)
                    return
                # Esperar justo hasta que venza la marca más vieja
                self.cond.wait(self.periodo - (ahora - self.marcas[0]))

    def try_acquire(self):
        """Versión no bloqueante: True si se pudo, False si se pasó del límite."""
        with self.cond:
            ahora = time.monotonic()
            self._limpiar(ahora)
            if len(self.marcas) < self.max_ops:
                self.marcas.append(ahora)
                return True
            return False

    __enter__ = acquire

    def __exit__(self, *args):
        pass


if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    num_threads = int(sys.argv[2]) if len(sys.argv) > 2 else 5
    ops = int(sys.argv[3]) if len(sys.argv) > 3 else 6

    limiter = RateLimiter(n)
    instantes = []
    lock = threading.Lock()
    inicio = time.monotonic()

    def worker(id):
        for i in range(ops):
            with limiter:
                t = time.monotonic() - inicio
                with lock:
                    instantes.append(t)
                print(f"[T{id}] op {i} en t={t:.3f}s")

    hilos = [threading.Thread(target=worker, args=(i,)) for i in range(num_threads)]
    for h in hilos:
        h.start()
    for h in hilos:
        h.join()

    total = len(instantes)
    print(f"\n{total} operaciones con límite {n}/s en {time.monotonic() - inicio:.2f}s")

    # Verificación: en ninguna ventana de 1 segundo puede haber más de N
    instantes.sort()
    peor = max(sum(1 for x in instantes if s <= x < s + 1.0) for s in instantes)
    print(f"Máximo de operaciones en cualquier ventana de 1s: {peor} "
          f"-> {'OK' if peor <= n else 'SE PASÓ'}")

    # try_acquire: ráfaga instantánea, solo pasan N
    rl = RateLimiter(n)
    pasaron = sum(rl.try_acquire() for _ in range(3 * n))
    print(f"try_acquire en ráfaga de {3 * n}: pasaron {pasaron} (esperado {n})")
