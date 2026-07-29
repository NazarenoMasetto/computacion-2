"""
Analizador 5: Señales de OTROS procesos (SigBlk/SigIgn/SigCgt/SigPnd).

Ojo: esto es distinto de manejador_senales.py, que maneja las señales
que recibe el PROPIO monitor (SIGINT, SIGHUP, SIGUSR1/2). Este módulo
solo LEE y decodifica el estado de señales de los procesos del sistema,
no reacciona a nada.
"""

import time
from recolector import listar_pids
from procfs import leer_status, decodificar_mascara


def analizador_senales(snapshot, intervalo_ref):
    while True:
        salida = []
        for pid in listar_pids():
            status = leer_status(pid)
            if not status:
                continue
            salida.append({
                'pid': pid,
                'bloqueadas': decodificar_mascara(status.get('SigBlk', '0')),
                'ignoradas': decodificar_mascara(status.get('SigIgn', '0')),
                'con_handler': decodificar_mascara(status.get('SigCgt', '0')),
                'pendientes': decodificar_mascara(status.get('SigPnd', '0')),
            })
        snapshot['senales'] = {'ts': time.time(), 'data': salida}
        time.sleep(intervalo_ref.value)
