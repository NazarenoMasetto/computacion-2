#!/usr/bin/env python3
"""Adicional: servidor eco de threads con comando STATS (protocolo por líneas).

Cada línea se devuelve tal cual, salvo `STATS`, que responde con clientes
activos, total atendidos, bytes transferidos y uptime.

Uso:
    python3 ad_stats.py [--port 8080]
    nc localhost 8080   ->  escribir líneas, y STATS
"""
import argparse
import socket
import threading
import time


class Estadisticas:
    """Contadores compartidos; todo acceso pasa por el lock."""

    def __init__(self):
        self.lock = threading.Lock()
        self.activos = 0
        self.atendidos = 0
        self.bytes = 0
        self.inicio = time.monotonic()

    def sumar(self, **deltas):
        with self.lock:
            for campo, d in deltas.items():
                setattr(self, campo, getattr(self, campo) + d)

    def resumen(self):
        with self.lock:   # foto consistente de los cuatro valores
            return (f'activos={self.activos} atendidos={self.atendidos} '
                    f'bytes={self.bytes} uptime={time.monotonic() - self.inicio:.1f}s')


def atender(conn, stats):
    stats.sumar(activos=1)
    try:
        with conn, conn.makefile('rb') as entrada:
            for linea in entrada:          # el archivo resuelve el framing por líneas
                stats.sumar(bytes=len(linea))
                if linea.strip().upper() == b'STATS':
                    respuesta = stats.resumen().encode() + b'\n'
                else:
                    respuesta = linea
                conn.sendall(respuesta)
                stats.sumar(bytes=len(respuesta))
    except (ConnectionResetError, BrokenPipeError):
        pass
    finally:
        stats.sumar(activos=-1, atendidos=1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--port', type=int, default=8080)
    args = ap.parse_args()
    stats = Estadisticas()
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as srv:
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind(('0.0.0.0', args.port))
        srv.listen(128)
        print(f'[stats] puerto {args.port}', flush=True)
        while True:
            conn, _ = srv.accept()
            threading.Thread(target=atender, args=(conn, stats), daemon=True).start()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('\nServidor detenido')
