"""
main.py

Entry point del monitor. Su único trabajo es orquestar:
  1. Crear el snapshot compartido (Manager.dict) y los intervalos (Value)
  2. Arrancar los 7 analizadores como procesos independientes
  3. Instalar el manejo de señales del monitor (self-pipe)
  4. Correr el loop principal: un solo select() que escucha tanto el
     teclado como el pipe de señales, y redibuja con Live/rich.

La lógica de "qué hace cada analizador" vive en analizadores/*.py,
la de "qué se dibuja" en display.py, y la de señales del propio monitor
en manejador_senales.py -- este archivo no repite nada de eso, solo
conecta las piezas.
"""

import os
import sys
import tty
import termios
import select
from multiprocessing import Process, Manager
from rich.live import Live

from analizadores.resumen import analizador_resumen
from analizadores.memoria import analizador_memoria
from analizadores.fds import analizador_fds
from analizadores.threads import analizador_threads
from analizadores.senales_proceso import analizador_senales
from analizadores.scheduling import analizador_scheduling
from analizadores.sistema import analizador_sistema

from procfs import leer_usuarios
from display import render, VISTAS
from manejador_senales import (
    leer_config, instalar_self_pipe, procesar_senales_pendientes,
    INTERVALOS_DEFAULT, INTERVALO_MIN, INTERVALO_MAX,
)

ORDEN_CICLO = ['cpu', 'rss', 'pid']

TARGETS = {
    'resumen': analizador_resumen, 'memoria': analizador_memoria,
    'fds': analizador_fds, 'threads': analizador_threads,
    'senales': analizador_senales, 'scheduling': analizador_scheduling,
    'sistema': analizador_sistema,
}


def main():
    manager = Manager()
    snapshot = manager.dict()

    config_inicial = leer_config()
    intervalos = {
        nombre: manager.Value('d', config_inicial['intervalos'].get(nombre, valor_default))
        for nombre, valor_default in INTERVALOS_DEFAULT.items()
    }

    procesos = []
    for nombre, funcion in TARGETS.items():
        p = Process(target=funcion, args=(snapshot, intervalos[nombre]), daemon=True)
        p.start()
        procesos.append(p)

    sig_read_fd = instalar_self_pipe()

    vista_actual = 'resumen'
    estado_senales = {'verbose': False, 'ultima_senal': None, 'ultimo_dump': None}
    estado_ui = {
        'seleccion': 0, 'pin_pid': None,
        'filtro_comando': config_inicial['filtros'].get('comando', ''),
        'filtro_uid': config_inicial['filtros'].get('uid'),
        'orden': 'cpu', 'modo_input': None, 'buffer_input': '', 'pids_visibles': [],
        'ayuda_visible': False,
    }
    mapa_usuarios_inv = {nombre: uid for uid, nombre in leer_usuarios().items()}

    fd_teclado = sys.stdin.fileno()
    config_original = termios.tcgetattr(fd_teclado)

    try:
        tty.setcbreak(fd_teclado)

        with Live(render(snapshot, vista_actual, estado_senales, estado_ui,
                         intervalos[vista_actual].value),
                  refresh_per_second=4, screen=True) as live:
            salir = False
            while not salir:
                listos, _, _ = select.select([fd_teclado, sig_read_fd], [], [], 0.3)

                if fd_teclado in listos:
                    tecla = os.read(fd_teclado, 1).decode(errors='ignore')

                    if estado_ui['ayuda_visible']:
                        # Con la ayuda abierta, cualquier tecla la cierra
                        # (salvo 'q', que además sale del programa).
                        estado_ui['ayuda_visible'] = False
                        if tecla.lower() == 'q':
                            salir = True

                    elif estado_ui['modo_input']:
                        if tecla in ('\r', '\n'):
                            texto = estado_ui['buffer_input'].strip()
                            if estado_ui['modo_input'] == 'comando':
                                estado_ui['filtro_comando'] = texto
                            else:
                                if texto == '':
                                    estado_ui['filtro_uid'] = None
                                elif texto.isdigit():
                                    estado_ui['filtro_uid'] = int(texto)
                                else:
                                    estado_ui['filtro_uid'] = mapa_usuarios_inv.get(texto, -1)
                            estado_ui['modo_input'] = None
                            estado_ui['buffer_input'] = ''
                        elif tecla == '\x1b':
                            estado_ui['modo_input'] = None
                            estado_ui['buffer_input'] = ''
                        elif tecla in ('\x7f', '\x08'):
                            estado_ui['buffer_input'] = estado_ui['buffer_input'][:-1]
                        elif tecla.isprintable():
                            estado_ui['buffer_input'] += tecla

                    elif tecla == '\x1b':
                        listos2, _, _ = select.select([fd_teclado], [], [], 0.05)
                        if listos2:
                            sig1 = os.read(fd_teclado, 1)
                            if sig1 == b'[':
                                sig2 = os.read(fd_teclado, 1)
                                if sig2 == b'A':
                                    estado_ui['seleccion'] = max(0, estado_ui['seleccion'] - 1)
                                elif sig2 == b'B':
                                    estado_ui['seleccion'] += 1

                    elif tecla.lower() == 'q':
                        salir = True
                    elif tecla in VISTAS:
                        vista_actual = VISTAS[tecla]
                        estado_ui['seleccion'] = 0
                    elif tecla in ('\r', '\n'):
                        visibles = estado_ui['pids_visibles']
                        if estado_ui['seleccion'] < len(visibles):
                            pid_sel = visibles[estado_ui['seleccion']]
                            estado_ui['pin_pid'] = (
                                None if estado_ui['pin_pid'] == pid_sel else pid_sel
                            )
                    elif tecla == '/':
                        estado_ui['modo_input'] = 'comando'
                        estado_ui['buffer_input'] = estado_ui['filtro_comando']
                    elif tecla == 'u':
                        estado_ui['modo_input'] = 'usuario'
                        estado_ui['buffer_input'] = ''
                    elif tecla == 'c':
                        idx = ORDEN_CICLO.index(estado_ui['orden'])
                        estado_ui['orden'] = ORDEN_CICLO[(idx + 1) % len(ORDEN_CICLO)]
                    elif tecla == '+':
                        ref = intervalos[vista_actual]
                        ref.value = min(INTERVALO_MAX, round(ref.value + 0.5, 2))
                    elif tecla == '-':
                        ref = intervalos[vista_actual]
                        minimo = INTERVALO_MIN.get(vista_actual, 0.5)
                        ref.value = max(minimo, round(ref.value - 0.5, 2))
                    elif tecla in ('h', '?'):
                        estado_ui['ayuda_visible'] = True

                if sig_read_fd in listos:
                    if procesar_senales_pendientes(sig_read_fd, snapshot, intervalos,
                                                    estado_ui, estado_senales):
                        salir = True

                if not salir:
                    live.update(render(snapshot, vista_actual, estado_senales, estado_ui,
                                       intervalos[vista_actual].value))

    finally:
        termios.tcsetattr(fd_teclado, termios.TCSADRAIN, config_original)
        print("\nCerrando analizadores...")
        for p in procesos:
            p.terminate()
        for p in procesos:
            p.join()
        print("Listo.")


if __name__ == '__main__':
    main()
