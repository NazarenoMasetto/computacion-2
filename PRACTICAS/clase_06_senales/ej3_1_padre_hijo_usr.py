#!/usr/bin/env python3
"""Ejercicio 3.1: el padre le manda comandos al hijo con SIGUSR1/SIGUSR2."""
import os
import signal
import time

contador = 0


def incrementar(sig, frame):
    """SIGUSR1: incrementa el contador del hijo."""
    global contador
    contador += 1
    print(f"[HIJO] Contador incrementado: {contador}", flush=True)


def mostrar(sig, frame):
    """SIGUSR2: muestra el valor actual."""
    print(f"[HIJO] Valor actual: {contador}", flush=True)


def main():
    # Registramos los handlers ANTES del fork: así no hay ventana en la que
    # el hijo existe pero todavía tiene la acción por defecto (que lo mataría)
    signal.signal(signal.SIGUSR1, incrementar)
    signal.signal(signal.SIGUSR2, mostrar)

    pid = os.fork()

    if pid == 0:
        # === HIJO ===
        print(f"[HIJO] PID={os.getpid()}, esperando señales...", flush=True)
        while True:
            signal.pause()  # Esperar señales (SIGTERM lo mata: acción por defecto)

    else:
        # === PADRE ===
        # El padre no usa USR1/USR2: vuelve a la acción por defecto
        signal.signal(signal.SIGUSR1, signal.SIG_DFL)
        signal.signal(signal.SIGUSR2, signal.SIG_DFL)
        time.sleep(0.5)  # Dar tiempo al hijo

        print("[PADRE] Enviando SIGUSR1 (incrementar) x3", flush=True)
        for _ in range(3):
            os.kill(pid, signal.SIGUSR1)
            time.sleep(0.3)

        print("[PADRE] Enviando SIGUSR2 (mostrar)", flush=True)
        os.kill(pid, signal.SIGUSR2)
        time.sleep(0.3)

        print("[PADRE] Enviando SIGUSR1 x2", flush=True)
        for _ in range(2):
            os.kill(pid, signal.SIGUSR1)
            time.sleep(0.3)

        print("[PADRE] Enviando SIGUSR2 (mostrar)", flush=True)
        os.kill(pid, signal.SIGUSR2)
        time.sleep(0.3)

        print("[PADRE] Terminando hijo", flush=True)
        os.kill(pid, signal.SIGTERM)
        _, status = os.wait()
        if os.WIFSIGNALED(status):
            print(f"[PADRE] Hijo terminó por {signal.Signals(os.WTERMSIG(status)).name}")


if __name__ == "__main__":
    main()
