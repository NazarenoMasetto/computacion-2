"""
recolector.py

El "Recolector" del diagrama de arquitectura: su única responsabilidad
es listar los PIDs activos del sistema leyendo /proc. Cada analizador
llama a listar_pids() al inicio de cada ciclo propio, en vez de tener
un proceso Recolector separado que reparta trabajo por Queue.

Nota de diseño (ver README): con 7 analizadores y listas de a lo sumo
unos cientos de PIDs, el costo de que cada analizador liste sus propios
PIDs es despreciable comparado con la complejidad de coordinar reparto
de trabajo entre un Recolector y 7 consumidores. Se prefirió simplicidad
architectural sobre un patrón productor/consumidor que no aportaba
beneficio real a esta escala.
"""

import os


def listar_pids():
    """Devuelve una lista de todos los PIDs actualmente activos,
    filtrando las entradas de /proc que no son numéricas (self,
    meminfo, cpuinfo, etc)."""
    pids = []
    for entrada in os.listdir('/proc'):
        if entrada.isdigit():
            pids.append(int(entrada))
    return pids
