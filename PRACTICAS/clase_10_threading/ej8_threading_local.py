#!/usr/bin/env python3
"""Ejercicio 8: threading.local() para que cada hilo (request) tenga su propio contexto."""
import random
import threading
import time

contexto = threading.local()


def get_contexto():
    """Devuelve el contexto del hilo actual (None si no se cargó)."""
    return {
        "usuario": getattr(contexto, "usuario", None),
        "ip": getattr(contexto, "ip", None),
        "timestamp": getattr(contexto, "timestamp", None),
    }


def procesar_logica():
    """Función 'profunda' que usa el contexto sin recibirlo por parámetro."""
    ctx = get_contexto()
    return f"{ctx['usuario']}@{ctx['ip']}"


def atender_request(request_id):
    contexto.usuario = f"user_{random.randint(1000, 9999)}"
    contexto.ip = f"192.168.{random.randint(0, 255)}.{random.randint(0, 255)}"
    contexto.timestamp = round(time.time(), 3)
    mio = (contexto.usuario, contexto.ip)

    print(f"[{threading.current_thread().name}] iniciando | contexto: {get_contexto()}")
    time.sleep(random.uniform(0.1, 0.5))  # mientras tanto, los otros hilos cargan su contexto

    # Verificamos que nadie nos pisó el contexto
    assert (contexto.usuario, contexto.ip) == mio
    print(f"[{threading.current_thread().name}] finalizando | {procesar_logica()}")


if __name__ == "__main__":
    hilos = [threading.Thread(target=atender_request, args=(i,), name=f"Request-{i}")
             for i in range(6)]
    for h in hilos:
        h.start()
    for h in hilos:
        h.join()

    # El hilo principal nunca cargó nada: su contexto está vacío
    print(f"\nContexto del hilo principal: {get_contexto()}")
    print("Todos los requests atendidos")
