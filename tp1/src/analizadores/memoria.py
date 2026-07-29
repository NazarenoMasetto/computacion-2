"""Analizador 2: Memoria (VmSize/VmRSS/etc, page faults, segmentos de maps)."""

import time
from recolector import listar_pids
from procfs import leer_stat_completo, leer_status, kb, leer_maps_agrupado


def analizador_memoria(snapshot, intervalo_ref):
    while True:
        salida = []
        for pid in listar_pids():
            status = leer_status(pid)
            st = leer_stat_completo(pid)
            if not status or not st:
                continue
            salida.append({
                'pid': pid, 'nombre': st['nombre'],
                'vmsize': kb(status, 'VmSize'), 'vmrss': kb(status, 'VmRSS'),
                'vmdata': kb(status, 'VmData'), 'vmstk': kb(status, 'VmStk'),
                'vmexe': kb(status, 'VmExe'), 'vmlib': kb(status, 'VmLib'),
                'vmhwm': kb(status, 'VmHWM'), 'vmswap': kb(status, 'VmSwap'),
                'minflt': st['minflt'], 'majflt': st['majflt'],
                'segmentos': leer_maps_agrupado(pid),
            })
        snapshot['memoria'] = {'ts': time.time(), 'data': salida}
        time.sleep(intervalo_ref.value)
