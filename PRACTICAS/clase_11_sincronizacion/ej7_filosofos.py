#!/usr/bin/env python3
"""Ejercicio 7: filósofos comensales, del deadlock a la solución.

Uso:
    python3 ej7_filosofos.py A              # versión ingenua + Barrier: se cuelga SIEMPRE (Ctrl+C)
    python3 ej7_filosofos.py A-sin-barrera  # ingenua sin barrera, 10 corridas con watchdog
    python3 ej7_filosofos.py B              # jerarquía de recursos (menor índice primero)
    python3 ej7_filosofos.py C              # ingenua + Semaphore(NUM - 1)
    python3 ej7_filosofos.py D              # comparación de tiempos y equidad entre B y C
"""
import random
import statistics
import sys
import threading
import time

NUM = 5
COMIDAS = 3


def pensar():
    time.sleep(random.uniform(0, 0.002))


def comer():
    time.sleep(random.uniform(0.001, 0.003))


# ---- Parte A: la versión que se cuelga ----
# Cada filósofo toma primero su tenedor izquierdo, después el derecho.
# La Barrier fuerza el entrelazado malo: nadie pide el derecho hasta que
# los cinco tienen el izquierdo.
tomaron_izq = threading.Barrier(NUM)


def filosofo_ingenuo(id, tenedores):
    for _ in range(COMIDAS):
        izq, der = id, (id + 1) % NUM
        with tenedores[izq]:
            tomaron_izq.wait()        # los 5 ya tienen su izquierdo
            with tenedores[der]:      # ...y ninguno va a conseguir el derecho
                print(f"Filósofo {id} come")


def parte_a():
    """Se cuelga siempre. Los threads son daemon para que Ctrl+C salga limpio."""
    tenedores = [threading.Lock() for _ in range(NUM)]
    hilos = [threading.Thread(target=filosofo_ingenuo, args=(i, tenedores), daemon=True)
             for i in range(NUM)]
    for h in hilos:
        h.start()
    print("Parte A: los 5 tomaron el izquierdo y esperan el derecho... (Ctrl+C para salir)")
    try:
        for h in hilos:
            h.join()
    except KeyboardInterrupt:
        print("\nInterrumpido: estaba en DEADLOCK.")


# ---- Estrategias para tomar los tenedores (sin barrera) ----
def tomar_ingenuo(id):
    """Izquierdo primero, después derecho."""
    return id, (id + 1) % NUM


def tomar_ordenado(id):
    """Parte B: primero el de MENOR índice (ordenamos índices, no Locks)."""
    izq, der = id, (id + 1) % NUM
    return min(izq, der), max(izq, der)


def cenar(estrategia, usar_semaforo=False, comidas=COMIDAS, duracion=None,
          timeout=5.0, verbose=False):
    """Corre una cena completa y devuelve métricas.

    - comidas: cuántas veces come cada uno (si duracion es None).
    - duracion: si se da, cada uno come todo lo que pueda durante esos segundos.
    Devuelve dict con: colgado, tiempo, comidas por filósofo y espera por filósofo.
    """
    tenedores = [threading.Lock() for _ in range(NUM)]
    sem = threading.Semaphore(NUM - 1) if usar_semaforo else None
    cuenta = [0] * NUM
    espera = [0.0] * NUM
    fin = None if duracion is None else time.perf_counter() + duracion

    def filosofo(id):
        primero, segundo = estrategia(id)
        while True:
            if fin is None and cuenta[id] >= comidas:
                break
            if fin is not None and time.perf_counter() >= fin:
                break
            pensar()
            t0 = time.perf_counter()
            if sem:
                sem.acquire()   # Parte C: como mucho 4 en la mesa
            try:
                with tenedores[primero]:
                    time.sleep(0)            # cede el GIL: favorece el entrelazado malo
                    with tenedores[segundo]:
                        espera[id] += time.perf_counter() - t0
                        if verbose:
                            print(f"Filósofo {id} come")
                        comer()
                        cuenta[id] += 1      # solo lo toca este thread
            finally:
                if sem:
                    sem.release()

    inicio = time.perf_counter()
    hilos = [threading.Thread(target=filosofo, args=(i,), daemon=True) for i in range(NUM)]
    for h in hilos:
        h.start()
    limite = timeout + (duracion or 0)
    for h in hilos:
        h.join(timeout=max(0.0, inicio + limite - time.perf_counter()))
    colgado = any(h.is_alive() for h in hilos)
    return {
        "colgado": colgado,
        "tiempo": time.perf_counter() - inicio,
        "comidas": cuenta,
        "espera": espera,
    }


def parte_a_sin_barrera(corridas=10):
    """Misma lógica ingenua sin barrera: casi nunca se cuelga."""
    colgadas = 0
    for i in range(corridas):
        r = cenar(tomar_ingenuo, timeout=2.0)
        colgadas += r["colgado"]
        print(f"  corrida {i + 1:2d}: {'COLGADA' if r['colgado'] else 'terminó'} "
              f"en {r['tiempo']:.3f}s")
    print(f"Se colgó {colgadas} de {corridas} veces.")


def parte_b_o_c(nombre, estrategia, semaforo):
    r = cenar(estrategia, usar_semaforo=semaforo, verbose=True)
    estado = "SE COLGÓ" if r["colgado"] else "terminó sin deadlock"
    print(f"{nombre}: {estado} en {r['tiempo']:.3f}s, comidas={r['comidas']}")


def parte_d(repeticiones=20, duracion=2.0):
    """Compara B y C: tiempo para 3 comidas y equidad en una cena larga."""
    soluciones = [("B jerarquía", tomar_ordenado, False),
                  ("C semáforo", tomar_ingenuo, True)]

    print(f"1) Tiempo para {COMIDAS} comidas por filósofo ({repeticiones} repeticiones)")
    for nombre, estr, sem in soluciones:
        tiempos = [cenar(estr, usar_semaforo=sem)["tiempo"] for _ in range(repeticiones)]
        print(f"   {nombre:12s}: promedio {statistics.mean(tiempos) * 1000:6.1f} ms  "
              f"(min {min(tiempos) * 1000:.1f}, max {max(tiempos) * 1000:.1f})")

    print(f"\n2) Equidad: cada uno come todo lo que puede durante {duracion}s")
    for nombre, estr, sem in soluciones:
        r = cenar(estr, usar_semaforo=sem, duracion=duracion)
        c = r["comidas"]
        esperas = [e / n * 1000 if n else 0 for e, n in zip(r["espera"], c)]
        print(f"   {nombre:12s}: comidas={c}  min/max={min(c) / max(c):.2f}  "
              f"desvío={statistics.pstdev(c):.1f}")
        print(f"   {'':12s}  espera media por comida (ms)="
              f"{[round(e, 2) for e in esperas]}")


if __name__ == "__main__":
    parte = sys.argv[1].upper() if len(sys.argv) > 1 else "D"
    if parte == "A":
        parte_a()
    elif parte == "A-SIN-BARRERA":
        parte_a_sin_barrera(int(sys.argv[2]) if len(sys.argv) > 2 else 10)
    elif parte == "B":
        parte_b_o_c("Parte B (jerarquía)", tomar_ordenado, False)
    elif parte == "C":
        parte_b_o_c("Parte C (semáforo N-1)", tomar_ingenuo, True)
    elif parte == "D":
        parte_d()
    else:
        print(__doc__)
