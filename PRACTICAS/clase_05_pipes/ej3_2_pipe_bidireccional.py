#!/usr/bin/env python3
"""Ejercicio 3.2: comunicación bidireccional con dos pipes.

Uso: python3 ej3_2_pipe_bidireccional.py [numero]   (por defecto 42)
"""
import os
import sys


def main(numero="42"):
    p2h_read, p2h_write = os.pipe()  # padre -> hijo
    h2p_read, h2p_write = os.pipe()  # hijo -> padre

    pid = os.fork()
    if pid == 0:
        # HIJO: cierra los extremos que no usa
        os.close(p2h_write)
        os.close(h2p_read)

        pregunta = os.read(p2h_read, 1024).decode().strip()
        print(f"[HIJO] Recibí pregunta: {pregunta}", flush=True)

        if pregunta.lstrip("-").isdigit():
            respuesta = str(int(pregunta) ** 2)
        else:
            respuesta = "No es un número"

        os.write(h2p_write, respuesta.encode())
        print(f"[HIJO] Envié respuesta: {respuesta}", flush=True)
        os.close(p2h_read)
        os.close(h2p_write)
        os._exit(0)

    # PADRE
    os.close(p2h_read)
    os.close(h2p_write)

    print(f"[PADRE] Enviando número: {numero}", flush=True)
    os.write(p2h_write, numero.encode())
    os.close(p2h_write)  # avisamos que no mandamos más

    respuesta = os.read(h2p_read, 1024).decode()
    print(f"[PADRE] Respuesta: {numero}² = {respuesta}")

    os.close(h2p_read)
    os.waitpid(pid, 0)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "42")
