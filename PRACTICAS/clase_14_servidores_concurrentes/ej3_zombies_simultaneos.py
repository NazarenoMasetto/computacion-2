#!/usr/bin/env python3
"""Ej 3 parte C: N hijos que mueren a la vez vs. un cosechador sin bucle.

Uso:
    python3 ej3_zombies_simultaneos.py            # handler SIN bucle
    python3 ej3_zombies_simultaneos.py --bucle    # handler CON bucle
    python3 ej3_zombies_simultaneos.py --repetir 5
"""
import argparse
import os
import signal
import subprocess
import time


def una_corrida(con_bucle, n=60):
    recogidos = [0]
    hijos = set()

    def cosechar(signum, frame):
        while True:
            try:
                pid, _ = os.waitpid(-1, os.WNOHANG)
            except ChildProcessError:
                return
            if pid in hijos:      # no contar al `ps` de subprocess
                recogidos[0] += 1
            if pid == 0 or not con_bucle:
                return      # sin bucle: un hijo por señal y listo

    signal.signal(signal.SIGCHLD, cosechar)
    for _ in range(n):
        pid = os.fork()
        if pid == 0:
            time.sleep(0.5)     # todos duermen lo mismo: mueren juntos
            os._exit(0)
        hijos.add(pid)

    time.sleep(2.0)
    # foto de los recogidos ANTES del ps: cuando ps termina llega otra SIGCHLD
    # y el handler sin bucle aprovecha para recoger un zombie más
    rec = recogidos[0]
    salida = subprocess.run(['ps', '--ppid', str(os.getpid()), '-o', 'stat='],
                            capture_output=True, text=True).stdout
    zombies = sum(1 for l in salida.splitlines() if l.strip().startswith('Z'))
    print(f'hijos={n}  recogidos={rec}  zombies={zombies}')

    # limpiar los que quedaron para que no contaminen la próxima corrida
    signal.signal(signal.SIGCHLD, signal.SIG_DFL)
    while True:
        try:
            os.waitpid(-1, 0)
        except ChildProcessError:
            break


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--bucle', action='store_true')
    ap.add_argument('--repetir', type=int, default=1)
    ap.add_argument('--hijos', type=int, default=60)
    args = ap.parse_args()
    print(f'Handler {"CON" if args.bucle else "SIN"} bucle')
    for _ in range(args.repetir):
        una_corrida(args.bucle, args.hijos)


if __name__ == '__main__':
    main()
