#!/usr/bin/env python3
"""
Adicional: "chat" primitivo entre dos procesos usando SharedMemory.

Distribución del segmento:
    byte 0      -> flag "hay mensaje nuevo" (0 = no, 1 = sí)
    byte 1      -> autor del último mensaje (0 = Ana, 1 = Beto)
    bytes 2-3   -> largo del mensaje (uint16)
    bytes 4...  -> texto del mensaje (UTF-8)

Por turnos: cada uno espera a que haya un mensaje nuevo del OTRO, lo lee y contesta.
El que escribe pone primero el texto, el largo y el autor, y el flag AL FINAL
(así el otro nunca ve un mensaje a medio escribir).

Uso: python3 adicional_chat_shm.py
"""
from multiprocessing import Process, shared_memory
import struct
import time

TAM_MENSAJE = 256
TAMAÑO = 4 + TAM_MENSAJE

NOMBRES = ["Ana", "Beto"]
GUION = {
    0: ["Hola Beto, ¿me leés?", "Todo bien, practicando memoria compartida", "Chau!"],
    1: ["Fuerte y claro, Ana. ¿Qué hacés?", "Genial, sin pipes ni sockets", "Chau Ana!"],
}


def escribir(buf, yo, texto):
    datos = texto.encode()[:TAM_MENSAJE]
    buf[4:4 + len(datos)] = datos
    struct.pack_into("H", buf, 2, len(datos))
    buf[1] = yo
    buf[0] = 1  # publicar: el flag va último


def esperar_mensaje(buf, yo):
    """Polling hasta que haya un mensaje nuevo que NO sea mío. Devuelve el texto."""
    while not (buf[0] == 1 and buf[1] != yo):
        time.sleep(0.01)
    largo = struct.unpack_from("H", buf, 2)[0]
    texto = bytes(buf[4:4 + largo]).decode()
    buf[0] = 0  # marcar como leído
    return texto


def participante(nombre_shm, yo, empiezo):
    shm = shared_memory.SharedMemory(name=nombre_shm)
    otro = NOMBRES[1 - yo]
    for i, frase in enumerate(GUION[yo]):
        if not (empiezo and i == 0):
            print(f"  [{NOMBRES[yo]}] leí de {otro}: {esperar_mensaje(shm.buf, yo)!r}", flush=True)
        print(f"[{NOMBRES[yo]}] escribo: {frase!r}", flush=True)
        escribir(shm.buf, yo, frase)
    if empiezo:
        # Quien empezó tiene que leer la última respuesta del otro
        print(f"  [{NOMBRES[yo]}] leí de {otro}: {esperar_mensaje(shm.buf, yo)!r}", flush=True)
    shm.close()


def main():
    shm = shared_memory.SharedMemory(create=True, size=TAMAÑO)
    shm.buf[:4] = b"\x00\x00\x00\x00"
    try:
        ana = Process(target=participante, args=(shm.name, 0, True))
        beto = Process(target=participante, args=(shm.name, 1, False))
        beto.start()
        ana.start()
        ana.join(timeout=10)
        beto.join(timeout=10)
        print("Chat terminado")
    finally:
        shm.close()
        shm.unlink()


if __name__ == "__main__":
    main()
