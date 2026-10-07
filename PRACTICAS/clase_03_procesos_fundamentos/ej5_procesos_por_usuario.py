#!/usr/bin/env python3
"""Ejercicio adicional: cantidad de procesos por usuario.

Recorre /proc, y para cada directorio numérico (un PID) lee el UID real
de la línea "Uid:" de /proc/<pid>/status. Después traduce el UID a nombre
con el módulo pwd.
Uso: python3 ej5_procesos_por_usuario.py
(Para comparar: ps -eo user= | sort | uniq -c | sort -rn)
"""

import os
import pwd
from collections import Counter


def uid_de(pid):
    """UID real del proceso, o None si terminó mientras lo leíamos."""
    try:
        with open(f"/proc/{pid}/status") as f:
            for linea in f:
                if linea.startswith("Uid:"):
                    return int(linea.split()[1])  # real, efectivo, saved, fs
    except (FileNotFoundError, ProcessLookupError, PermissionError):
        return None
    return None


def nombre_usuario(uid):
    try:
        return pwd.getpwuid(uid).pw_name
    except KeyError:
        return str(uid)  # UID sin entrada en /etc/passwd (ej. dentro de contenedores)


def main():
    conteo = Counter()
    for entrada in os.listdir("/proc"):
        if entrada.isdigit():
            uid = uid_de(entrada)
            if uid is not None:
                conteo[nombre_usuario(uid)] += 1

    print(f"{'USUARIO':<20} {'PROCESOS':>8}")
    for usuario, cantidad in conteo.most_common():
        print(f"{usuario:<20} {cantidad:>8}")
    print(f"{'TOTAL':<20} {sum(conteo.values()):>8}")


if __name__ == "__main__":
    main()
