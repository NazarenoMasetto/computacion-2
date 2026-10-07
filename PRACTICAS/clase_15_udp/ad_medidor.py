#!/usr/bin/env python3
"""Adicional: medidor de pérdida, desorden y jitter (iperf en miniatura).

El emisor manda N datagramas numerados [seq !I][timestamp !d] a intervalo fijo.
El receptor cuenta perdidos, desordenados, duplicados y calcula el jitter
(variación de los tiempos entre llegadas, y el estimador de la RFC 3550).

Uso:
    python3 ad_medidor.py receptor [--port 8085]
    python3 ad_medidor.py emisor   [--port 8085] [--n 1000] [--intervalo 0.001]
                                   [--perdida 0] [--desorden 0]
--perdida/--desorden simulan una red mala del lado del emisor.
"""
import argparse
import random
import socket
import statistics
import struct
import time

FORMATO = '!Id'            # seq (4 bytes) + timestamp (8 bytes)
FIN = 0xFFFFFFFF           # seq especial: "terminé, mandé N"


def receptor(puerto):
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(('0.0.0.0', puerto))
        print(f'[medidor] receptor en {puerto}', flush=True)
        while True:
            vistos, llegadas = set(), []
            desordenados = duplicados = 0
            mayor = -1
            jitter_rfc = 0.0
            transito_ant = None
            while True:
                datos, origen = s.recvfrom(1024)
                seq, ts = struct.unpack(FORMATO, datos[:12])
                ahora = time.time()
                if seq == FIN:
                    total = int(ts)
                    break
                if seq in vistos:
                    duplicados += 1
                    continue
                vistos.add(seq)
                if seq < mayor:
                    desordenados += 1
                mayor = max(mayor, seq)
                llegadas.append(ahora)
                # RFC 3550: J += (|D| - J) / 16, D = diferencia de tiempos de tránsito
                transito = ahora - ts
                if transito_ant is not None:
                    jitter_rfc += (abs(transito - transito_ant) - jitter_rfc) / 16
                transito_ant = transito
            entre = [b - a for a, b in zip(llegadas, llegadas[1:])]
            perdidos = total - len(vistos)
            print(f'De {origen}: enviados={total} recibidos={len(vistos)} '
                  f'perdidos={perdidos} ({perdidos / max(total, 1):.1%}) '
                  f'desordenados={desordenados} duplicados={duplicados}')
            if len(entre) > 1:
                print(f'  entre llegadas: media={statistics.mean(entre) * 1000:.3f} ms '
                      f'desvío (jitter)={statistics.stdev(entre) * 1000:.3f} ms  '
                      f'jitter RFC3550={jitter_rfc * 1000:.3f} ms', flush=True)


def emisor(args):
    destino = ('localhost', args.port)
    retenido = None     # para simular desorden: retener uno y mandarlo después
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        for seq in range(args.n):
            paquete = struct.pack(FORMATO, seq, time.time())
            if random.random() >= args.perdida:
                if retenido is None and random.random() < args.desorden:
                    retenido = paquete
                else:
                    s.sendto(paquete, destino)
                    if retenido is not None:
                        s.sendto(retenido, destino)
                        retenido = None
            time.sleep(args.intervalo)
        if retenido is not None:
            s.sendto(retenido, destino)
        time.sleep(0.1)
        s.sendto(struct.pack(FORMATO, FIN, args.n), destino)
    print(f'Mandé {args.n} datagramas cada {args.intervalo * 1000:.1f} ms')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('rol', choices=['receptor', 'emisor'])
    ap.add_argument('--port', type=int, default=8085)
    ap.add_argument('--n', type=int, default=1000)
    ap.add_argument('--intervalo', type=float, default=0.001)
    ap.add_argument('--perdida', type=float, default=0.0)
    ap.add_argument('--desorden', type=float, default=0.0)
    args = ap.parse_args()
    if args.rol == 'receptor':
        receptor(args.port)
    else:
        emisor(args)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('\nCortado')
