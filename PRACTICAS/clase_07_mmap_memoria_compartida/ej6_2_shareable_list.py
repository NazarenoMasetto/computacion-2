#!/usr/bin/env python3
"""Ejercicio 6.2: ShareableList para compartir datos de distintos tipos."""
from multiprocessing import Process, shared_memory


def actualizar_datos(nombre_shm):
    """Actualiza datos en la lista compartida."""
    sl = shared_memory.ShareableList(name=nombre_shm)

    # Modificar valores (cada posición mantiene el tipo con el que se creó)
    sl[0] = 42              # int
    sl[1] = 3.14159         # float
    sl[2] = "actualizado"   # str (máx largo del original)
    sl[3] = False           # bool

    print(f"[WORKER] Lista actualizada: {list(sl)}")
    sl.shm.close()


def main():
    # OJO: el tipo y tamaño máximo de cada elemento se fija en la creación.
    # En la consigna se reservan 10 espacios y "actualizado" tiene 11: funciona
    # solo porque ShareableList redondea el lugar a múltiplos de 8 bytes (10 -> 16).
    # Un string de 17+ tiraría ValueError, así que reservamos 15 a propósito.
    sl = shared_memory.ShareableList(
        [0, 0.0, " " * 15, True],
        name="mi_lista_comp"
    )
    try:
        print(f"Antes:   {list(sl)}")

        p = Process(target=actualizar_datos, args=(sl.shm.name,))
        p.start()
        p.join()

        print(f"Después: {list(sl)}")
    finally:
        sl.shm.close()
        sl.shm.unlink()


if __name__ == "__main__":
    main()
