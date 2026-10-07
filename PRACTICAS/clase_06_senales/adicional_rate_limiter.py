#!/usr/bin/env python3
"""
Adicional: rate limiter con SIGALRM (máximo N operaciones por segundo).

Uso: python3 adicional_rate_limiter.py [N] [segundos]     (default: N=5, 5 segundos)

Funciona como un "balde de fichas": cada SIGALRM (una vez por segundo, con setitimer)
recarga el balde a N fichas. Cada operación gasta una ficha; si no hay, espera.
"""
import signal
import sys
import time

fichas = 0
max_por_segundo = 5
hechas_en_este_segundo = 0
segundo = 0


def recargar(sig, frame):
    """Handler de SIGALRM: reporta el segundo que pasó y recarga las fichas."""
    global fichas, hechas_en_este_segundo, segundo
    segundo += 1
    print(f"  -- segundo {segundo}: {hechas_en_este_segundo} operaciones (límite {max_por_segundo})")
    hechas_en_este_segundo = 0
    fichas = max_por_segundo


def operacion(i):
    """La operación 'limitada' (acá no hace nada costoso, iría lo más rápido posible)."""
    print(f"op {i:3d} a los {time.monotonic() - inicio:5.2f}s")


def esperar_ficha():
    """Bloquea hasta que haya una ficha disponible y la consume."""
    global fichas, hechas_en_este_segundo
    while fichas == 0:
        # Polling cortito: con signal.pause() habría una carrera (si la alarma llega
        # entre el chequeo y el pause, nos quedaríamos dormidos un segundo de más)
        time.sleep(0.005)
    fichas -= 1
    hechas_en_este_segundo += 1


def main():
    global fichas, max_por_segundo, inicio
    sys.stdout.reconfigure(line_buffering=True)
    max_por_segundo = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    duracion = float(sys.argv[2]) if len(sys.argv) > 2 else 5

    signal.signal(signal.SIGALRM, recargar)
    fichas = max_por_segundo
    inicio = time.monotonic()
    signal.setitimer(signal.ITIMER_REAL, 1.0, 1.0)  # SIGALRM cada 1 segundo

    print(f"Rate limiter: máximo {max_por_segundo} ops/s durante {duracion}s")
    i = 0
    try:
        while time.monotonic() - inicio < duracion:
            esperar_ficha()
            operacion(i)
            i += 1
    except KeyboardInterrupt:
        pass
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)  # apagar el timer

    total = time.monotonic() - inicio
    print(f"Total: {i} operaciones en {total:.2f}s ({i / total:.2f} ops/s)")


inicio = 0.0

if __name__ == "__main__":
    main()
