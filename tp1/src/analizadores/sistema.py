"""Analizador 7: Stats globales del sistema (CPU, load, memoria, procesos)."""

import time
from recolector import listar_pids
from procfs import (
    leer_stat_completo, leer_cpu_global, leer_loadavg, leer_meminfo,
    leer_uptime, leer_btime,
)


def analizador_sistema(snapshot, intervalo_ref):
    cpu_anterior = leer_cpu_global()
    btime = leer_btime()  # no cambia nunca mientras el sistema está prendido
    while True:
        cpu_ahora = leer_cpu_global()
        cpu_pct = {'user': 0.0, 'system': 0.0, 'idle': 0.0, 'iowait': 0.0}
        if cpu_anterior:
            deltas = [a - b for a, b in zip(cpu_ahora, cpu_anterior)]
            total = sum(deltas)
            if total > 0:
                cpu_pct['user'] = round(deltas[0] / total * 100, 1)
                cpu_pct['system'] = round(deltas[2] / total * 100, 1)
                cpu_pct['idle'] = round(deltas[3] / total * 100, 1)
                cpu_pct['iowait'] = round(deltas[4] / total * 100, 1)
        cpu_anterior = cpu_ahora

        total_procesos = 0
        zombies = 0
        threads_totales = 0
        for pid in listar_pids():
            st = leer_stat_completo(pid)
            if not st:
                continue
            total_procesos += 1
            threads_totales += st['num_threads']
            if st['estado'] == 'Z':
                zombies += 1

        mem = leer_meminfo()
        snapshot['sistema'] = {
            'ts': time.time(),
            'data': {
                'cpu_pct': cpu_pct, 'load': leer_loadavg(),
                'mem_total_kb': mem.get('MemTotal', 0), 'mem_free_kb': mem.get('MemFree', 0),
                'mem_buffers_kb': mem.get('Buffers', 0), 'mem_cached_kb': mem.get('Cached', 0),
                'swap_total_kb': mem.get('SwapTotal', 0), 'swap_free_kb': mem.get('SwapFree', 0),
                'total_procesos': total_procesos, 'zombies': zombies,
                'threads_totales': threads_totales, 'uptime_seg': leer_uptime(),
                'btime': btime,
            }
        }
        time.sleep(intervalo_ref.value)
