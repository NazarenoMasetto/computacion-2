#!/usr/bin/env python3
"""Ejercicio 3.1: comunicación básica padre <- hijo por un pipe."""
import os


def main():
    # El pipe se crea ANTES del fork para que ambos hereden los extremos
    read_fd, write_fd = os.pipe()

    pid = os.fork()
    if pid == 0:
        # HIJO: escribe
        os.close(read_fd)  # no lee
        mensajes = ["Mensaje 1 del hijo", "Mensaje 2 del hijo", "Mensaje 3 del hijo", "FIN"]
        for msg in mensajes:
            os.write(write_fd, (msg + "\n").encode())
            print(f"[HIJO] Envié: {msg}", flush=True)
        os.close(write_fd)  # al cerrar, el padre va a recibir EOF
        os._exit(0)

    # PADRE: lee
    os.close(write_fd)  # si no lo cierro, nunca llega el EOF
    print("[PADRE] Esperando mensajes del hijo...\n", flush=True)

    buffer = b""
    while True:
        datos = os.read(read_fd, 1024)
        if not datos:  # EOF: todos los extremos de escritura están cerrados
            break
        buffer += datos

    for msg in buffer.decode().strip().split("\n"):
        print(f"[PADRE] Recibí: {msg}")

    os.close(read_fd)
    os.waitpid(pid, 0)
    print("\n[PADRE] Hijo terminó")


if __name__ == "__main__":
    main()
