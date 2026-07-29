"""Analizador 1: Resumen (estado, CPU%, PPID, UID, threads, nombre)."""

import time
from recolector import listar_pids
from procfs import leer_stat_completo, leer_status, HZ


def analizador_resumen(snapshot, intervalo_ref):
    anterior = {}  # pid -> (jiffies_totales, timestamp) de la lectura previa
    while True:
        ahora = time.time()
        salida = []
        for pid in listar_pids():
            st = leer_stat_completo(pid)
            if not st:
                continue
            status = leer_status(pid)
            uid = 0
            if status and 'Uid' in status:
                uid = int(status['Uid'].split()[0])

            jt = st['utime'] + st['stime']
            cpu_pct = 0.0
            if pid in anterior:
                jprev, tprev = anterior[pid]
                dj = jt - jprev
                dt = ahora - tprev
                if dt > 0:
                    cpu_pct = (dj / HZ) / dt * 100
            anterior[pid] = (jt, ahora)

            salida.append({
                'pid': st['pid'], 'ppid': st['ppid'], 'uid': uid,
                'threads': st['num_threads'], 'estado': st['estado'],
                'nombre': st['nombre'], 'cpu_pct': round(cpu_pct, 1),
            })

        snapshot['resumen'] = {'ts': ahora, 'data': salida}
        time.sleep(intervalo_ref.value)
