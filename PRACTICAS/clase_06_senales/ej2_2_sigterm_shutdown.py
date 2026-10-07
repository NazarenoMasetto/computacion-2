#!/usr/bin/env python3
"""Ejercicio 2.2: shutdown limpio con SIGTERM/SIGINT (libera recursos antes de salir)."""
import signal
import time
import os


class Aplicacion:
    def __init__(self):
        self.ejecutando = True
        self.recursos = []

        # Registrar manejadores
        signal.signal(signal.SIGTERM, self.shutdown)
        signal.signal(signal.SIGINT, self.shutdown)

    def shutdown(self, sig, frame):
        # El handler solo marca la bandera; el cleanup lo hace el loop principal
        nombre_señal = signal.Signals(sig).name
        print(f"\nRecibí {nombre_señal}, cerrando...")
        self.ejecutando = False

    def adquirir_recurso(self, nombre):
        print(f"Adquiriendo recurso: {nombre}")
        self.recursos.append(nombre)

    def liberar_recursos(self):
        # Se liberan en orden inverso al que se adquirieron
        for recurso in reversed(self.recursos):
            print(f"Liberando recurso: {recurso}")
            time.sleep(0.3)
        self.recursos.clear()

    def run(self):
        print(f"PID: {os.getpid()}")
        print(f"Enviá 'kill {os.getpid()}' para terminar limpiamente")

        # Simular adquisición de recursos
        self.adquirir_recurso("base_de_datos")
        self.adquirir_recurso("archivo_log")
        self.adquirir_recurso("conexion_red")

        # Loop principal
        while self.ejecutando:
            print("Trabajando...")
            time.sleep(1)

        # Cleanup
        self.liberar_recursos()
        print("Aplicación terminada correctamente")


if __name__ == "__main__":
    app = Aplicacion()
    app.run()
