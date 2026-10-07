#!/usr/bin/env python3
"""Adicional: scheduler con prioridades.

En lugar de la deque se usa un heap (heapq) ordenado por "tiempo virtual":
cada tarea, al reanudarse, avanza su tiempo virtual en 1/peso. Las de más
peso avanzan más despacio, así que vuelven a quedar primeras más seguido
(es la idea del CFS de Linux, en miniatura).

Uso:
    python3 scheduler_prioridades.py
"""
import heapq
import itertools
from collections import Counter


def tarea(nombre, pasos):
    for _ in range(pasos):
        yield nombre                 # devuelve su nombre para contar turnos


def scheduler_prioridades(tareas_con_peso, turnos_max=None):
    """tareas_con_peso: lista de (peso, generador). Devuelve el orden de turnos."""
    desempate = itertools.count()    # para no comparar generadores en el heap
    heap = [(0.0, next(desempate), peso, t) for peso, t in tareas_con_peso]
    heapq.heapify(heap)
    orden = []
    while heap and (turnos_max is None or len(orden) < turnos_max):
        virtual, _, peso, t = heapq.heappop(heap)
        try:
            orden.append(next(t))
            heapq.heappush(heap, (virtual + 1 / peso, next(desempate), peso, t))
        except StopIteration:
            pass
    return orden


def main():
    tareas = [(3, tarea('ALTA', 100)), (2, tarea('media', 100)), (1, tarea('baja', 100))]
    orden = scheduler_prioridades(tareas, turnos_max=30)
    print('Primeros 30 turnos:')
    print('  ' + ' '.join(n[0] for n in orden))
    print('Turnos por tarea:', dict(Counter(orden)), '(proporción 3:2:1)')


if __name__ == '__main__':
    main()
