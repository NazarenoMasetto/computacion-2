#!/usr/bin/env python3
"""Ejercicio 4: pool de conexiones limitado con Semaphore."""
import random
import threading
import time


class ConnectionPool:
    """Pool de `size` conexiones: el semáforo cuenta las libres."""

    def __init__(self, size):
        self.size = size
        self.semaforo = threading.Semaphore(size)
        self.conexiones_disponibles = list(range(size))
        self.lock = threading.Lock()  # protege la lista y las estadísticas
        self.en_uso = 0
        self.max_en_uso = 0
        self.estadisticas = {
            "total_requests": 0,
            "esperas": 0,
            "tiempo_total_espera": 0,
        }

    def obtener(self, timeout=None):
        inicio = time.time()
        if self.semaforo.acquire(timeout=timeout):
            tiempo_espera = time.time() - inicio
            with self.lock:
                conn_id = self.conexiones_disponibles.pop(0)
                self.en_uso += 1
                self.max_en_uso = max(self.max_en_uso, self.en_uso)
                self.estadisticas["total_requests"] += 1
                if tiempo_espera > 0.01:
                    self.estadisticas["esperas"] += 1
                    self.estadisticas["tiempo_total_espera"] += tiempo_espera
            return conn_id
        return None

    def liberar(self, conn_id):
        with self.lock:
            self.conexiones_disponibles.append(conn_id)
            self.en_uso -= 1
        self.semaforo.release()

    def mostrar_estadisticas(self):
        print("\n=== Estadísticas del pool ===")
        print(f"Total requests: {self.estadisticas['total_requests']}")
        print(f"Requests que esperaron: {self.estadisticas['esperas']}")
        if self.estadisticas['esperas'] > 0:
            prom = self.estadisticas['tiempo_total_espera'] / self.estadisticas['esperas']
            print(f"Tiempo promedio espera: {prom:.3f}s")
        print(f"Máximo de conexiones en uso a la vez: {self.max_en_uso} (límite {self.size})")


# Pool de 3 conexiones
pool = ConnectionPool(3)


def cliente(id):
    for _ in range(3):
        conn = pool.obtener(timeout=5)
        if conn is not None:
            print(f"[Cliente {id}] Obtuvo conexión {conn}")
            time.sleep(random.uniform(0.5, 1.5))  # Usar conexión
            pool.liberar(conn)
            print(f"[Cliente {id}] Liberó conexión {conn}")
        else:
            print(f"[Cliente {id}] Timeout esperando conexión")
        time.sleep(random.uniform(0.1, 0.3))


if __name__ == "__main__":
    # 10 clientes compitiendo por 3 conexiones
    threads = [threading.Thread(target=cliente, args=(i,)) for i in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    pool.mostrar_estadisticas()
