#!/usr/bin/env python3
"""
Adicional: watchdog que monitorea un proceso y lo reinicia si termina inesperadamente.

Uso:
    python3 adicional_watchdog.py                     # vigila un worker de prueba que a veces falla
    python3 adicional_watchdog.py -- sleep 30          # vigila cualquier comando

"Inesperadamente" = sale con código != 0 o muere por una señal que no mandó el watchdog.
Si el proceso sale con código 0 se considera terminado bien y no se reinicia.
Para parar todo: kill <pid_watchdog> (le reenvía SIGTERM al hijo y sale).
Para simular una caída: kill -9 <pid_hijo>
"""
import os
import signal
import sys
import time

MAX_REINICIOS = 5

# Worker de prueba: trabaja unos segundos y a veces falla
WORKER_PRUEBA = [
    sys.executable, "-c",
    "import os, random, time\n"
    "print(f'  [worker {os.getpid()}] arrancando', flush=True)\n"
    "time.sleep(random.uniform(1, 3))\n"
    "codigo = random.choice([0, 1, 1])\n"
    "print(f'  [worker {os.getpid()}] saliendo con código {codigo}', flush=True)\n"
    "raise SystemExit(codigo)\n",
]

detener = False
pid_hijo = None


def manejar_salida(sig, frame):
    """SIGTERM/SIGINT al watchdog: dejar de vigilar y bajar al hijo."""
    global detener
    detener = True
    print(f"\n[WATCHDOG] Recibí {signal.Signals(sig).name}, terminando al hijo...")
    if pid_hijo is not None:
        try:
            os.kill(pid_hijo, signal.SIGTERM)
        except ProcessLookupError:
            pass


def lanzar(comando):
    """fork + exec del comando a vigilar. Devuelve el pid del hijo."""
    pid = os.fork()
    if pid == 0:
        # El hijo vuelve a la acción por defecto (exec igual resetea los handlers)
        signal.signal(signal.SIGINT, signal.SIG_DFL)
        try:
            os.execvp(comando[0], comando)
        except OSError as e:
            print(f"[WATCHDOG] No se pudo ejecutar {comando[0]}: {e}", file=sys.stderr)
            os._exit(127)
    return pid


def describir(status):
    if os.WIFEXITED(status):
        return f"salió con código {os.WEXITSTATUS(status)}"
    return f"murió por {signal.Signals(os.WTERMSIG(status)).name}"


def main():
    global pid_hijo
    sys.stdout.reconfigure(line_buffering=True)

    args = sys.argv[1:]
    if args and args[0] == "--":
        args = args[1:]
    comando = args if args else WORKER_PRUEBA

    signal.signal(signal.SIGTERM, manejar_salida)
    signal.signal(signal.SIGINT, manejar_salida)

    print(f"[WATCHDOG] PID {os.getpid()} (kill {os.getpid()} para terminar)")
    reinicios = 0
    while not detener:
        pid_hijo = lanzar(comando)
        print(f"[WATCHDOG] Hijo lanzado con PID {pid_hijo}")

        # waitpid bloqueante: si llega una señal, el handler corre y
        # waitpid se reintenta solo (PEP 475) hasta que el hijo termine
        _, status = os.waitpid(pid_hijo, 0)
        pid_hijo = None
        print(f"[WATCHDOG] El hijo {describir(status)}")

        if detener:
            break
        if os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0:
            print("[WATCHDOG] Terminó bien, no hace falta reiniciar")
            break
        if reinicios >= MAX_REINICIOS:
            print(f"[WATCHDOG] Se alcanzó el máximo de {MAX_REINICIOS} reinicios, me rindo")
            break

        reinicios += 1
        print(f"[WATCHDOG] Terminación inesperada -> reinicio #{reinicios} en 1s")
        time.sleep(1)

    print(f"[WATCHDOG] Fin (reinicios realizados: {reinicios})")


if __name__ == "__main__":
    main()
