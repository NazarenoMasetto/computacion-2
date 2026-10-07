#!/usr/bin/env python3
"""Ejercicio 4: ping-pong padre <-> hijo con multiprocessing.Pipe() (bidireccional)."""
import multiprocessing
import os

RONDAS = 5


def hijo(conn):
    """Recibe un ping y contesta con un pong, RONDAS veces."""
    for _ in range(RONDAS):
        msg = conn.recv()
        print(f"    [Hijo {os.getpid()}] recibí: {msg}", flush=True)
        conn.send(f"pong {msg.split()[1]}")
    conn.close()


def main():
    # duplex=True (por defecto): los dos extremos pueden enviar y recibir
    conn_padre, conn_hijo = multiprocessing.Pipe()
    p = multiprocessing.Process(target=hijo, args=(conn_hijo,))
    p.start()
    conn_hijo.close()  # el padre no usa el extremo del hijo

    for i in range(1, RONDAS + 1):
        conn_padre.send(f"ping {i}")
        print(f"[Padre {os.getpid()}] envié: ping {i}", flush=True)
        respuesta = conn_padre.recv()
        print(f"[Padre] recibí: {respuesta}", flush=True)

    conn_padre.close()
    p.join()
    print(f"Ping-pong terminado ({RONDAS} rondas, {RONDAS * 2} mensajes)")


if __name__ == "__main__":
    main()
