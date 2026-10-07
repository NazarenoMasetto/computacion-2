#!/usr/bin/env python3
"""Benchmark: lanza N clientes eco simultáneos y mide latencias (versión propia).

Uso:
    python3 benchmark.py [--port 8080] [--clientes 20] [--timeout 30]
"""
import argparse
import socket
import statistics
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor


def un_cliente(host, puerto, mensaje, timeout):
    """Conecta, manda, espera el eco completo. Devuelve (ok, segundos, error)."""
    inicio = time.perf_counter()
    try:
        with socket.create_connection((host, puerto), timeout=timeout) as s:
            s.sendall(mensaje)
            recibido = b''
            while len(recibido) < len(mensaje):
                pedazo = s.recv(4096)
                if not pedazo:
                    break
                recibido += pedazo
        ok = recibido == mensaje
        return ok, time.perf_counter() - inicio, None if ok else 'eco incompleto'
    except Exception as e:
        return False, time.perf_counter() - inicio, type(e).__name__


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--host', default='localhost')
    ap.add_argument('--port', '--puerto', type=int, default=8080)
    ap.add_argument('--clientes', type=int, default=50)
    ap.add_argument('--timeout', type=float, default=30.0)
    args = ap.parse_args()

    mensaje = b'x' * 256
    print(f'Lanzando {args.clientes} clientes simultáneos contra {args.host}:{args.port}')
    inicio = time.perf_counter()
    with ThreadPoolExecutor(max_workers=args.clientes) as pool:
        resultados = list(pool.map(
            lambda _: un_cliente(args.host, args.port, mensaje, args.timeout),
            range(args.clientes)))
    total = time.perf_counter() - inicio

    ok = [r for r in resultados if r[0]]
    fallidos = [r for r in resultados if not r[0]]
    lat = sorted(r[1] for r in ok)
    print(f'Completados:      {len(ok)}/{args.clientes}')
    print(f'Tiempo total:     {total:.2f}s')
    if lat:
        print(f'Latencia mínima:  {lat[0]:.3f}s')
        print(f'Latencia mediana: {statistics.median(lat):.3f}s')
        print(f'Latencia máxima:  {lat[-1]:.3f}s')
        print(f'Throughput:       {len(ok) / total:.1f} clientes/s')
    if fallidos:
        print(f'Fallidos: {len(fallidos)}')
        for motivo, n in Counter(r[2] for r in fallidos).items():
            print(f'  {motivo}: {n}')
    # latencias muy escalonadas = atención en serie
    if len(lat) >= 4 and lat[-1] - lat[0] > 0.5 * lat[-1]:
        print(f'Nota: latencias de {lat[0]:.2f}s a {lat[-1]:.2f}s -> atención en serie')


if __name__ == '__main__':
    main()
