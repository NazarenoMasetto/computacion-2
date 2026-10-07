#!/usr/bin/env python3
"""Cliente de prueba: abre N conexiones a la vez y mide cuánto tarda cada una.

Cada conexión manda una línea y espera la respuesta (hasta que el servidor
cierre o llegue un '\\n'). Sirve para comparar servidor secuencial contra
concurrente (ej. 1.3 y 2.B) y para lanzar muchas conexiones (ej. 1.5).

Uso:
    python3 cliente_medir.py [-n 2] [--port 8080] [--mensaje hola]
"""
import argparse
import socket
import threading
import time


def una_conexion(i, host, puerto, mensaje, t0, resultados):
    try:
        with socket.create_connection((host, puerto), timeout=30) as s:
            s.sendall(mensaje.encode() + b'\n')
            respuesta = s.makefile('rb').readline()
        resultados[i] = (time.perf_counter() - t0, respuesta.decode().strip())
    except OSError as e:
        resultados[i] = (time.perf_counter() - t0, f'ERROR {e}')


def main():
    parser = argparse.ArgumentParser(description='Conexiones simultáneas')
    parser.add_argument('-n', type=int, default=2, help='cantidad de clientes')
    parser.add_argument('--host', default='localhost')
    parser.add_argument('--port', type=int, default=8080)
    parser.add_argument('--mensaje', default='hola')
    parser.add_argument('--resumen', action='store_true',
                        help='no listar cada cliente, solo el total')
    args = parser.parse_args()

    resultados = [None] * args.n
    t0 = time.perf_counter()
    hilos = [threading.Thread(target=una_conexion,
                              args=(i, args.host, args.port, args.mensaje,
                                    t0, resultados))
             for i in range(args.n)]
    for h in hilos:
        h.start()
    for h in hilos:
        h.join()

    if not args.resumen:
        for i, (t, resp) in enumerate(resultados, 1):
            print(f'cliente {i}: {t:5.2f}s  -> {resp}')
    print(f'total: {time.perf_counter() - t0:.2f}s')
    return resultados


if __name__ == '__main__':
    main()
