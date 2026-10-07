#!/usr/bin/env python3
"""Ejercicio 4.1 - Monitor de cambios en tiempo real (por polling).

Guarda una "foto" del directorio (nombre -> inodo, tamaño, mtime), espera
un intervalo, saca otra foto y compara. Los renombres se detectan porque el
inodo se mantiene con otro nombre. Usamos polling para no depender de
librerías externas (inotify-simple no es stdlib).

Ejemplos:
    python3 watch.py /var/log
    python3 watch.py . --interval 0.5 --recursive
"""

import argparse
import os
import sys
import time
from datetime import datetime


def foto(base: str, recursivo: bool) -> dict[str, tuple[int, int, float]]:
    """{ruta_relativa: (inodo, tamaño, mtime)}."""
    estado = {}
    if recursivo:
        for raiz, dirs, archivos in os.walk(base, onerror=lambda e: None):
            for n in dirs + archivos:
                ruta = os.path.join(raiz, n)
                try:
                    st = os.lstat(ruta)
                except OSError:
                    continue
                estado[os.path.relpath(ruta, base)] = (st.st_ino, st.st_size, st.st_mtime)
    else:
        try:
            with os.scandir(base) as it:
                for e in it:
                    try:
                        st = e.stat(follow_symlinks=False)
                    except OSError:
                        continue
                    estado[e.name] = (st.st_ino, st.st_size, st.st_mtime)
        except OSError:
            pass
    return estado


def comparar(antes: dict, ahora: dict) -> list[str]:
    """Devuelve una lista de mensajes describiendo los cambios."""
    eventos = []
    borrados = {n: v for n, v in antes.items() if n not in ahora}
    creados = {n: v for n, v in ahora.items() if n not in antes}

    # Renombres: mismo inodo, nombre distinto
    inodo_borrado = {v[0]: n for n, v in borrados.items()}
    for nombre, valor in list(creados.items()):
        viejo = inodo_borrado.get(valor[0])
        if viejo is not None:
            eventos.append(f"RENOMBRADO: {viejo} -> {nombre}")
            del creados[nombre]
            del borrados[viejo]

    for nombre in sorted(creados):
        eventos.append(f"CREADO: {nombre}")
    for nombre in sorted(borrados):
        eventos.append(f"ELIMINADO: {nombre}")
    for nombre in sorted(set(antes) & set(ahora)):
        (_, t1, m1), (_, t2, m2) = antes[nombre], ahora[nombre]
        if t1 != t2:
            eventos.append(f"MODIFICADO: {nombre} (tamaño: {t1} -> {t2})")
        elif m1 != m2:
            eventos.append(f"MODIFICADO: {nombre} (fecha de modificación)")
    return eventos


def main() -> int:
    parser = argparse.ArgumentParser(description="Monitorea cambios en un directorio")
    parser.add_argument("directorio")
    parser.add_argument("--interval", type=float, default=1.0, help="segundos entre chequeos")
    parser.add_argument("--recursive", "-r", action="store_true", help="incluir subdirectorios")
    args = parser.parse_args()

    if not os.path.isdir(args.directorio):
        print(f"Error: '{args.directorio}' no es un directorio o no existe", file=sys.stderr)
        return 1

    print(f"Monitoreando {args.directorio} (Ctrl+C para salir)\n", flush=True)
    anterior = foto(args.directorio, args.recursive)
    try:
        while True:
            time.sleep(args.interval)
            if not os.path.isdir(args.directorio):
                print("El directorio monitoreado desapareció. Saliendo.")
                return 1
            actual = foto(args.directorio, args.recursive)
            hora = datetime.now().strftime("%H:%M:%S")
            for evento in comparar(anterior, actual):
                print(f"[{hora}] {evento}", flush=True)
            anterior = actual
    except KeyboardInterrupt:
        print("\nMonitoreo finalizado.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
