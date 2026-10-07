#!/usr/bin/env python3
"""
Ejercicio de síntesis: banco con cuentas en memoria compartida.
Múltiples procesos (cajeros) realizan transferencias.

NOTA: Este ejercicio intencionalmente NO usa sincronización
para que puedas observar las race conditions.

Uso:
    python3 sintesis_banco.py                         # 100 transferencias por cajero
    python3 sintesis_banco.py 10000                   # tarea 2: más transferencias
    python3 sintesis_banco.py 100 /tmp/banco.log      # tarea 3: con log de transferencias
"""
from multiprocessing import Process, Array
import os
import random
import sys

NUM_CUENTAS = 5
SALDO_INICIAL = 1000
NUM_PROCESOS = 3


def mostrar_saldos(cuentas, etiqueta):
    """Muestra los saldos de todas las cuentas."""
    saldos = [cuentas[i] for i in range(NUM_CUENTAS)]
    total = sum(saldos)
    print(f"[{etiqueta}] Saldos: {saldos} | Total: {total}")


def cajero(cuentas, cajero_id, num_transferencias, archivo_log=None):
    """Un cajero que realiza transferencias entre cuentas."""
    log = None
    if archivo_log:
        # Modo 'a' = O_APPEND: cada write va al final del archivo de forma atómica,
        # así las líneas de distintos cajeros no se pisan entre sí
        log = open(archivo_log, "a", buffering=1)

    realizadas = 0
    for _ in range(num_transferencias):
        # Elegir dos cuentas diferentes al azar
        origen = random.randint(0, NUM_CUENTAS - 1)
        destino = random.randint(0, NUM_CUENTAS - 1)
        while destino == origen:
            destino = random.randint(0, NUM_CUENTAS - 1)

        # Transferir un monto aleatorio
        monto = random.randint(1, 50)

        if cuentas[origen] >= monto:
            # Estas dos operaciones NO son atómicas
            cuentas[origen] -= monto
            cuentas[destino] += monto
            realizadas += 1
            if log:
                log.write(f"cajero={cajero_id} pid={os.getpid()} "
                          f"origen={origen} destino={destino} monto={monto}\n")

    if log:
        log.close()
    print(f"[Cajero {cajero_id}] Completó {num_transferencias} intentos "
          f"({realizadas} transferencias hechas)")


def main():
    transferencias = int(sys.argv[1]) if len(sys.argv) > 1 else 100
    archivo_log = sys.argv[2] if len(sys.argv) > 2 else None
    if archivo_log:
        open(archivo_log, "w").close()  # empezar con el log vacío

    # Crear array compartido con saldos iniciales
    cuentas = Array('i', [SALDO_INICIAL] * NUM_CUENTAS)

    print(f"=== Banco con {NUM_CUENTAS} cuentas ===")
    print(f"=== Saldo total esperado: {NUM_CUENTAS * SALDO_INICIAL} ===\n")

    mostrar_saldos(cuentas, "INICIO")

    # Lanzar cajeros
    procesos = []
    for i in range(NUM_PROCESOS):
        p = Process(target=cajero, args=(cuentas, i, transferencias, archivo_log))
        p.start()
        procesos.append(p)

    for p in procesos:
        p.join()

    mostrar_saldos(cuentas, "FINAL")

    # Verificar integridad
    total_final = sum(cuentas[i] for i in range(NUM_CUENTAS))
    total_esperado = NUM_CUENTAS * SALDO_INICIAL

    if total_final != total_esperado:
        print(f"\n¡ERROR! Se perdieron ${total_esperado - total_final} "
              "(si es negativo, apareció plata de la nada)")
        print("Esto es una race condition - se necesita sincronización")
    else:
        print("\nTodo correcto (pero fue suerte - ejecutalo varias veces)")

    if archivo_log:
        with open(archivo_log) as f:
            lineas = f.readlines()
        print(f"\nLog: {len(lineas)} transferencias registradas en {archivo_log}")
        for linea in lineas[:3]:
            print(f"  {linea.rstrip()}")


if __name__ == "__main__":
    main()
