#!/usr/bin/env python3
"""
Adicional: extensión del ejercicio 5 donde varias SIGUSR1 seguidas son comandos distintos.

    1 x USR1  -> mostrar estadísticas
    2 x USR1  -> resetear estadísticas
    3 x USR1  -> pausar / reanudar el procesamiento
    (HUP, USR2 y TERM/INT funcionan igual que en servidor_signals.py)

Las USR1 se cuentan dentro de una ventana de 0.7 s: cada USR1 reinicia un timer
(setitimer) y cuando el timer vence (SIGALRM) se ejecuta el comando según la cantidad.

Ejemplo desde otra terminal (2 USR1 seguidas):
    kill -USR1 <pid>; kill -USR1 <pid>
"""
import signal
import sys
import time

from servidor_signals import Servidor

VENTANA = 0.7  # segundos para agrupar USR1 consecutivas


class ServidorComandos(Servidor):
    def __init__(self):
        self.pulsos_usr1 = 0
        self.pausado = False
        super().__init__()

    def _registrar_manejadores(self):
        super()._registrar_manejadores()
        # Reemplazamos USR1 por el contador y agregamos SIGALRM para cerrar la ventana
        signal.signal(signal.SIGUSR1, self._contar_usr1)
        signal.signal(signal.SIGALRM, self._ejecutar_comando)

    def _contar_usr1(self, sig, frame):
        self.pulsos_usr1 += 1
        print(f"\n[SIGUSR1] pulso #{self.pulsos_usr1}")
        # Reiniciar la ventana: el comando se decide cuando dejen de llegar USR1
        signal.setitimer(signal.ITIMER_REAL, VENTANA)

    def _ejecutar_comando(self, sig, frame):
        n = self.pulsos_usr1
        self.pulsos_usr1 = 0
        if n == 1:
            print("[CMD] 1 x USR1 -> estadísticas")
            self._mostrar_stats(sig, frame)
        elif n == 2:
            print("[CMD] 2 x USR1 -> reseteo estadísticas")
            self.stats = {"requests": 0, "errores": 0, "inicio": time.time()}
        elif n == 3:
            self.pausado = not self.pausado
            print(f"[CMD] 3 x USR1 -> {'PAUSADO' if self.pausado else 'REANUDADO'}")
        else:
            print(f"[CMD] {n} x USR1 -> comando desconocido, ignorado")

    def procesar_request(self):
        if self.pausado:
            time.sleep(0.1)  # no procesa nada mientras está en pausa
            return
        super().procesar_request()

    def run(self):
        print("Comandos con USR1: 1 = stats, 2 = reset stats, 3 = pausa/reanudar")
        super().run()


if __name__ == "__main__":
    sys.stdout.reconfigure(line_buffering=True)
    ServidorComandos().run()
