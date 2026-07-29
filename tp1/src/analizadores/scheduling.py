"""Analizador 6: Scheduling (nice, priority, policy, affinity, ctx switches)."""

import time
from recolector import listar_pids
from procfs import leer_stat_completo, leer_status, POLICIES


def analizador_scheduling(snapshot, intervalo_ref):
    while True:
        salida = []
        for pid in listar_pids():
            st = leer_stat_completo(pid)
            status = leer_status(pid)
            if not st or not status:
                continue
            salida.append({
                'pid': pid, 'nombre': st['nombre'], 'nice': st['nice'],
                'priority': st['priority'],
                'policy': POLICIES.get(st['policy'], f"?({st['policy']})"),
                'rt_priority': st['rt_priority'],
                'affinity': status.get('Cpus_allowed_list', '?'),
                'vol_ctxt': status.get('voluntary_ctxt_switches', '0'),
                'nonvol_ctxt': status.get('nonvoluntary_ctxt_switches', '0'),
                'session': st['session'], 'pgrp': st['pgrp'],
            })
        snapshot['scheduling'] = {'ts': time.time(), 'data': salida}
        time.sleep(intervalo_ref.value)
