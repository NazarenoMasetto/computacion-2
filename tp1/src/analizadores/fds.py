"""Analizador 3: File Descriptors abiertos por proceso."""

import os
import time
from recolector import listar_pids
from procfs import clasificar_fd


def analizador_fds(snapshot, intervalo_ref):
    while True:
        salida = []
        for pid in listar_pids():
            try:
                fds = os.listdir(f'/proc/{pid}/fd')
            except (FileNotFoundError, ProcessLookupError, PermissionError, OSError):
                continue
            lista_fds = []
            for fd in fds:
                try:
                    destino = os.readlink(f'/proc/{pid}/fd/{fd}')
                except (FileNotFoundError, ProcessLookupError, PermissionError, OSError):
                    continue
                lista_fds.append({'fd': fd, 'destino': destino, 'tipo': clasificar_fd(destino)})
            if lista_fds:
                salida.append({'pid': pid, 'cantidad': len(lista_fds), 'fds': lista_fds})
        snapshot['fds'] = {'ts': time.time(), 'data': salida}
        time.sleep(intervalo_ref.value)
