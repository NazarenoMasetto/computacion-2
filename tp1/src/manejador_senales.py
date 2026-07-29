"""
manejador_senales.py

Maneja las señales que recibe el MONITOR (no las de otros procesos,
eso está en analizadores/senales_proceso.py):

  SIGINT / SIGTERM -> shutdown limpio
  SIGHUP           -> recarga config.json (intervalos y filtros default)
  SIGUSR1          -> dump del snapshot a dump_<timestamp>.json
  SIGUSR2          -> toggle de modo verbose
  SIGWINCH         -> repintar (terminal redimensionada)

Usa el patrón self-pipe (signal.set_wakeup_fd): el handler de Python no
hace ningún trabajo pesado, solo dejamos que el SO escriba 1 byte al
pipe. El procesamiento real ocurre en el loop principal, cuando select()
avisa que el pipe tiene datos -- así los handlers son async-signal-safe.
"""

import os
import time
import json
import signal

CONFIG_PATH = 'config.json'

INTERVALOS_DEFAULT = {
    'resumen': 2.0, 'memoria': 3.0, 'fds': 5.0, 'threads': 2.0,
    'senales': 10.0, 'scheduling': 10.0, 'sistema': 2.0,
}

INTERVALO_MIN = {
    'resumen': 0.5, 'memoria': 1.0, 'fds': 2.0, 'threads': 0.5,
    'senales': 5.0, 'scheduling': 5.0, 'sistema': 1.0,
}
INTERVALO_MAX = 30.0

FILTROS_DEFAULT = {'comando': '', 'uid': None}


def leer_config():
    """Lee config.json si existe; si no, devuelve los defaults.
    Se llama al arrancar Y cada vez que llega SIGHUP. Devuelve un dict
    con 'intervalos' y 'filtros' (ambos con fallback a los defaults si
    el archivo no existe, está corrupto, o le faltan claves)."""
    intervalos = dict(INTERVALOS_DEFAULT)
    filtros = dict(FILTROS_DEFAULT)

    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, 'r') as f:
                data = json.load(f)
            intervalos.update(data.get('intervalos', {}))
            filtros.update(data.get('filtros', {}))
        except (json.JSONDecodeError, OSError):
            pass

    return {'intervalos': intervalos, 'filtros': filtros}


def aplicar_config(intervalos_refs, estado_ui, config):
    """Actualiza EN CALIENTE tanto los intervalos (Value compartidos,
    sin reiniciar procesos) como los filtros default de la TUI."""
    for nombre, valor in config.get('intervalos', {}).items():
        if nombre in intervalos_refs:
            intervalos_refs[nombre].value = float(valor)

    filtros = config.get('filtros', {})
    if 'comando' in filtros:
        estado_ui['filtro_comando'] = filtros['comando']
    if 'uid' in filtros:
        estado_ui['filtro_uid'] = filtros['uid']


def volcar_snapshot(snapshot):
    """SIGUSR1: guarda el snapshot actual a un JSON con timestamp.
    Devuelve (nombre_archivo, error) -- si algo falla, el mensaje real
    viene en error en vez de desaparecer en silencio."""
    ts = int(time.time())
    nombre_archivo = os.path.join(os.getcwd(), f'dump_{ts}.json')
    try:
        copia = {clave: snapshot[clave] for clave in snapshot.keys()}
        with open(nombre_archivo, 'w') as f:
            json.dump(copia, f, indent=2, default=str)
        return nombre_archivo, None
    except Exception as e:
        return None, f'{type(e).__name__}: {e}'


def instalar_self_pipe():
    """Arma el pipe y registra los handlers no-op para las señales del
    monitor. Devuelve el file descriptor de lectura, que el loop
    principal agrega a su select()."""
    sig_read_fd, sig_write_fd = os.pipe()
    os.set_blocking(sig_write_fd, False)
    signal.set_wakeup_fd(sig_write_fd)

    def manejador_noop(signum, frame):
        pass  # el byte ya lo escribió set_wakeup_fd solo

    senales_monitoreadas = [signal.SIGINT, signal.SIGTERM, signal.SIGHUP,
                             signal.SIGUSR1, signal.SIGUSR2]
    if hasattr(signal, 'SIGWINCH'):  # no existe en Windows, pero esto es Linux-only
        senales_monitoreadas.append(signal.SIGWINCH)

    for s in senales_monitoreadas:
        signal.signal(s, manejador_noop)

    return sig_read_fd


def procesar_senales_pendientes(sig_read_fd, snapshot, intervalos, estado_ui, estado_senales):
    """Lee los bytes acumulados en el pipe y aplica la acción de cada
    señal recibida. Devuelve True si el monitor debe cerrarse
    (SIGINT/SIGTERM)."""
    salir = False
    crudo = os.read(sig_read_fd, 8)  # puede traer varias señales juntas
    for b in crudo:
        numero_senal = b
        try:
            nombre_senal = signal.Signals(numero_senal).name
        except ValueError:
            nombre_senal = f'SIG{numero_senal}'
        estado_senales['ultima_senal'] = nombre_senal

        if numero_senal in (signal.SIGINT, signal.SIGTERM):
            salir = True
        elif numero_senal == signal.SIGHUP:
            aplicar_config(intervalos, estado_ui, leer_config())
        elif numero_senal == signal.SIGUSR1:
            archivo, error = volcar_snapshot(snapshot)
            estado_senales['ultimo_dump'] = f'OK: {archivo}' if archivo else f'ERROR: {error}'
        elif numero_senal == signal.SIGUSR2:
            estado_senales['verbose'] = not estado_senales['verbose']
        elif hasattr(signal, 'SIGWINCH') and numero_senal == signal.SIGWINCH:
            pass  # no hace falta acción extra: el loop principal ya
            # repinta con Live en cada vuelta, y rich relee el tamaño
            # real de la terminal en cada render. Solo dejamos
            # constancia de que la señal se recibió (ultima_senal).

    return salir
