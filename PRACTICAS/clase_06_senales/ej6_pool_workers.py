#!/usr/bin/env python3
"""
Ejercicio 6.1: pool de workers supervisado con señales.
El supervisor reinicia workers que terminan (bien o con error).
Uso: python3 ej6_pool_workers.py [num_workers]    (terminar: kill <pid_supervisor> o Ctrl+C)
"""
import os
import signal
import sys
import time
import random


class WorkerPool:
    def __init__(self, num_workers):
        self.num_workers = num_workers
        self.workers = {}  # pid -> info
        self.ejecutando = True

        signal.signal(signal.SIGTERM, self._shutdown)
        signal.signal(signal.SIGINT, self._shutdown)
        signal.signal(signal.SIGCHLD, self._sigchld)

    def _shutdown(self, sig, frame):
        print("\n[SUPERVISOR] Shutdown solicitado")
        self.ejecutando = False
        # Enviar SIGTERM a todos los workers
        for pid in list(self.workers.keys()):
            try:
                os.kill(pid, signal.SIGTERM)
            except ProcessLookupError:
                pass

    def _sigchld(self, sig, frame):
        # Loop con WNOHANG: un solo SIGCHLD puede representar varios hijos muertos
        while True:
            try:
                pid, status = os.waitpid(-1, os.WNOHANG)
                if pid == 0:
                    break
                if pid in self.workers:
                    info = self.workers.pop(pid)
                    codigo = os.WEXITSTATUS(status) if os.WIFEXITED(status) else -1
                    print(f"[SUPERVISOR] Worker {info['id']} (pid {pid}) terminó con código {codigo}")
            except ChildProcessError:
                break

    def _worker_main(self, worker_id):
        """Código que ejecuta cada worker."""
        # El hijo hereda los handlers del supervisor: los reemplazamos.
        # SIGINT se ignora (Ctrl+C le llega a todo el grupo; el supervisor
        # se encarga de mandarnos SIGTERM) y SIGCHLD vuelve al default.
        signal.signal(signal.SIGINT, signal.SIG_IGN)
        signal.signal(signal.SIGCHLD, signal.SIG_DFL)
        signal.pthread_sigmask(signal.SIG_UNBLOCK, {signal.SIGCHLD})

        def worker_shutdown(sig, frame):
            print(f"[Worker {worker_id}] Recibí SIGTERM, terminando...")
            sys.stdout.flush()
            os._exit(0)

        signal.signal(signal.SIGTERM, worker_shutdown)
        print(f"[Worker {worker_id}] Iniciado (PID {os.getpid()})")

        # Simular trabajo
        for i in range(random.randint(5, 15)):
            print(f"[Worker {worker_id}] Trabajando... ({i})")
            time.sleep(0.5)

        # Simular fallo ocasional
        if random.random() < 0.3:
            print(f"[Worker {worker_id}] ¡Error simulado!")
            sys.stdout.flush()
            os._exit(1)

        print(f"[Worker {worker_id}] Trabajo completado")
        sys.stdout.flush()
        os._exit(0)

    def spawn_worker(self, worker_id):
        # Bloqueamos SIGCHLD mientras hacemos fork y registramos el pid:
        # si el hijo muriera antes de estar en self.workers, el handler lo ignoraría
        signal.pthread_sigmask(signal.SIG_BLOCK, {signal.SIGCHLD})
        try:
            pid = os.fork()
            if pid == 0:
                self._worker_main(worker_id)
            else:
                self.workers[pid] = {"id": worker_id, "started": time.time()}
                print(f"[SUPERVISOR] Spawned worker {worker_id} (PID {pid})")
        finally:
            signal.pthread_sigmask(signal.SIG_UNBLOCK, {signal.SIGCHLD})

    def run(self):
        print(f"[SUPERVISOR] PID {os.getpid()}, iniciando {self.num_workers} workers")

        # Iniciar workers
        for i in range(self.num_workers):
            self.spawn_worker(i)

        # Loop supervisor: reiniciar workers caídos
        next_worker_id = self.num_workers
        while self.ejecutando:
            time.sleep(1)

            # ¿Necesitamos más workers?
            if len(self.workers) < self.num_workers and self.ejecutando:
                print(f"[SUPERVISOR] Solo {len(self.workers)} workers activos, spawneando más")
                self.spawn_worker(next_worker_id)
                next_worker_id += 1

        # Esperar que terminen todos
        while self.workers:
            time.sleep(0.1)

        print("[SUPERVISOR] Todos los workers terminados")


if __name__ == "__main__":
    sys.stdout.reconfigure(line_buffering=True)
    cantidad = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    pool = WorkerPool(cantidad)
    pool.run()
