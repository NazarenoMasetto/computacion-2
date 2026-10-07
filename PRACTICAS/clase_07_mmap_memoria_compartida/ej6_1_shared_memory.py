#!/usr/bin/env python3
"""Ejercicio 6.1: compartir datos con SharedMemory entre un productor y un consumidor."""
from multiprocessing import Process, shared_memory
import struct
import time


def productor(shm_name, num_valores):
    """Produce valores en la memoria compartida."""
    shm = shared_memory.SharedMemory(name=shm_name)  # se "engancha" por nombre

    for i in range(num_valores):
        struct.pack_into('i', shm.buf, i * 4, i * i)

    # Marcar como listo (último byte) recién después de escribir todo
    shm.buf[-1] = 1

    print(f"[PRODUCTOR] Escribí {num_valores} valores")
    shm.close()


def consumidor(shm_name, num_valores):
    """Lee valores de la memoria compartida."""
    shm = shared_memory.SharedMemory(name=shm_name)

    # Esperar a que el productor termine (polling simple)
    while shm.buf[-1] != 1:
        time.sleep(0.01)

    valores = []
    for i in range(num_valores):
        val = struct.unpack_from('i', shm.buf, i * 4)[0]
        valores.append(val)

    print(f"[CONSUMIDOR] Leí: {valores}")
    shm.close()


def main():
    # Crear memoria compartida: NUM enteros + 1 byte de flag
    num = 10
    shm = shared_memory.SharedMemory(create=True, size=num * 4 + 1)
    print(f"Segmento creado: {shm.name} (visible en /dev/shm/{shm.name})")
    try:
        p_prod = Process(target=productor, args=(shm.name, num))
        p_cons = Process(target=consumidor, args=(shm.name, num))

        p_cons.start()  # arranca primero a propósito: tiene que esperar el flag
        p_prod.start()

        p_prod.join()
        p_cons.join()
    finally:
        # close() en cada proceso; unlink() una sola vez, el creador
        shm.close()
        shm.unlink()


if __name__ == "__main__":
    main()
