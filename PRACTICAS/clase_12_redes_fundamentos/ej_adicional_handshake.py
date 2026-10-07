#!/usr/bin/env python3
"""Ejercicio adicional: medir el costo del handshake TCP.

Mide cuánto tarda socket.create_connection() (DNS ya resuelto aparte, así
medimos solo el handshake) contra un servidor local y uno remoto.

Uso:
    python3 ej_adicional_handshake.py [--remoto HOST:PUERTO] [--local-puerto P] [-n N]
"""
import argparse
import socket
import statistics
import threading
import time


def servidor_local(puerto, listo):
    """Servidor mínimo que acepta y cierra conexiones (corre en un thread)."""
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(("127.0.0.1", puerto))
    srv.listen(128)
    listo.set()
    while True:
        conn, _ = srv.accept()
        conn.close()


def medir(ip, puerto, n):
    """Devuelve la lista de tiempos (ms) de n conexiones."""
    tiempos = []
    for _ in range(n):
        t0 = time.perf_counter()
        s = socket.create_connection((ip, puerto), timeout=5)
        tiempos.append((time.perf_counter() - t0) * 1000)
        s.close()
    return tiempos


def resumen(nombre, tiempos):
    print(f"{nombre:28s}: mediana {statistics.median(tiempos):8.3f} ms  "
          f"min {min(tiempos):8.3f}  max {max(tiempos):8.3f}")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--remoto", default="example.com:80")
    p.add_argument("--local-puerto", type=int, default=8080)
    p.add_argument("-n", type=int, default=20)
    args = p.parse_args()

    listo = threading.Event()
    threading.Thread(target=servidor_local, args=(args.local_puerto, listo),
                     daemon=True).start()
    listo.wait()
    resumen(f"local 127.0.0.1:{args.local_puerto}",
            medir("127.0.0.1", args.local_puerto, args.n))

    host, puerto = args.remoto.rsplit(":", 1)
    try:
        t0 = time.perf_counter()
        ip = socket.gethostbyname(host)          # DNS aparte, para no mezclarlo
        print(f"(DNS de {host} -> {ip} tardó {(time.perf_counter() - t0) * 1000:.1f} ms)")
        resumen(f"remoto {ip}:{puerto}", medir(ip, int(puerto), args.n))
    except OSError as e:
        print(f"No se pudo medir el remoto {args.remoto}: {e}")
