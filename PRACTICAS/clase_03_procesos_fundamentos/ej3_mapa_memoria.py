#!/usr/bin/env python3
"""Ejercicio 3: identificar text / data / heap / stack / librerías en /proc/<pid>/maps.

Si no se pasa un PID, lanza "python3 -c 'import time; time.sleep(60)'"
como en la consigna, analiza su mapa y lo termina.
Uso: python3 ej3_mapa_memoria.py [pid]
"""

import os
import subprocess
import sys
import time


def clasificar(perms, ruta, ejecutable):
    """Devuelve una etiqueta para la región según permisos y nombre."""
    if ruta == "[heap]":
        return "HEAP"
    if ruta == "[stack]":
        return "STACK"
    if ruta in ("[vdso]", "[vvar]", "[vsyscall]") or ruta.startswith("[vvar"):
        return "KERNEL (vdso/vvar)"
    if ruta == ejecutable:
        if "x" in perms:
            return "TEXT del ejecutable"
        if "w" in perms:
            return "DATA/BSS del ejecutable"
        return "ejecutable solo lectura (headers/rodata)"
    if ".so" in ruta:
        return "librería compartida" + (" (código)" if "x" in perms else "")
    if ruta == "":
        return "anónima (mmap, datos/bss extra)"
    return "archivo mapeado"


def analizar(pid):
    # El ejecutable real del proceso (python3 es un symlink, por eso readlink)
    ejecutable = os.readlink(f"/proc/{pid}/exe")
    print(f"PID {pid} - ejecutable: {ejecutable}\n")
    resumen = {}
    with open(f"/proc/{pid}/maps") as f:
        for linea in f:
            campos = linea.split()
            rango, perms = campos[0], campos[1]
            ruta = campos[5] if len(campos) >= 6 else ""
            inicio, fin = (int(x, 16) for x in rango.split("-"))
            tam_kb = (fin - inicio) // 1024
            etiqueta = clasificar(perms, ruta, ejecutable)
            resumen[etiqueta] = resumen.get(etiqueta, 0) + tam_kb
            # Mostramos todo salvo el montón de librerías, que es largo
            if not etiqueta.startswith("librería"):
                print(f"{rango:<34} {perms} {tam_kb:>8} KB  {etiqueta:<40} {ruta}")
    print("\nResumen por tipo de región (KB):")
    for etiqueta, kb in sorted(resumen.items(), key=lambda x: -x[1]):
        print(f"  {etiqueta:<40} {kb:>10}")


def main():
    if len(sys.argv) > 1:
        analizar(int(sys.argv[1]))
        return
    hijo = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(60)"])
    time.sleep(0.5)  # esperar a que cargue el intérprete
    try:
        analizar(hijo.pid)
    finally:
        hijo.terminate()
        hijo.wait()


if __name__ == "__main__":
    main()
