"""Analizador 4: Threads (LWPs) de cada proceso, vía /proc/<pid>/task."""

import os
import time
from recolector import listar_pids
from procfs import leer_stat_thread, leer_comm_thread, HZ


def analizador_threads(snapshot, intervalo_ref):
    anterior = {}  # (pid, tid) -> (jiffies_totales, timestamp)
    while True:
        ahora = time.time()
        salida = []
        for pid in listar_pids():
            try:
                tids = os.listdir(f'/proc/{pid}/task')
            except (FileNotFoundError, ProcessLookupError, PermissionError, OSError):
                continue
            threads_pid = []
            for tid in tids:
                st = leer_stat_thread(pid, tid)
                if not st:
                    continue
                nombre = leer_comm_thread(pid, tid)
                jt = st['utime'] + st['stime']
                clave = (pid, tid)
                cpu_pct = 0.0
                if clave in anterior:
                    jprev, tprev = anterior[clave]
                    dj = jt - jprev
                    dt = ahora - tprev
                    if dt > 0:
                        cpu_pct = (dj / HZ) / dt * 100
                anterior[clave] = (jt, ahora)
                threads_pid.append({'tid': int(tid), 'nombre': nombre,
                                     'estado': st['estado'], 'cpu_pct': round(cpu_pct, 1)})
            if threads_pid:
                salida.append({'pid': pid, 'threads': threads_pid})
        snapshot['threads'] = {'ts': ahora, 'data': salida}
        time.sleep(intervalo_ref.value)
