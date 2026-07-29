"""
procfs.py

Helpers "puros" para leer y parsear archivos de /proc. Ninguna función
de este módulo sabe nada de multiprocessing, snapshots ni TUI -- solo
reciben un PID (o nada) y devuelven datos ya parseados en dicts/listas
de Python. Esto es intencional: separa "cómo se lee /proc" de
"qué hace cada analizador con esos datos".
"""

import os
import signal

HZ = os.sysconf('SC_CLK_TCK')  # jiffies por segundo del sistema

POLICIES = {0: 'OTHER', 1: 'FIFO', 2: 'RR', 3: 'BATCH', 5: 'IDLE'}


def leer_stat_completo(pid):
    """Lee /proc/<pid>/stat y devuelve los campos que usan los
    distintos analizadores (resumen, memoria, scheduling)."""
    try:
        with open(f'/proc/{pid}/stat', 'r') as f:
            contenido = f.read()
    except (FileNotFoundError, ProcessLookupError, OSError):
        return None

    inicio_nombre = contenido.index('(')
    fin_nombre = contenido.rindex(')')
    pid_campo = contenido[:inicio_nombre].strip()
    nombre = contenido[inicio_nombre + 1:fin_nombre]
    resto = contenido[fin_nombre + 1:].split()

    def campo(i, default=0, tipo=int):
        try:
            return tipo(resto[i])
        except (IndexError, ValueError):
            return default

    return {
        'pid': int(pid_campo), 'nombre': nombre,
        'estado': campo(0, '?', str), 'ppid': campo(1), 'pgrp': campo(2),
        'session': campo(3), 'minflt': campo(7), 'cminflt': campo(8),
        'majflt': campo(9), 'cmajflt': campo(10), 'utime': campo(11),
        'stime': campo(12), 'priority': campo(15), 'nice': campo(16),
        'num_threads': campo(17), 'rt_priority': campo(37), 'policy': campo(38),
    }


def leer_status(pid):
    """Lee /proc/<pid>/status: formato clave-valor, mucho más simple
    de parsear que /proc/<pid>/stat."""
    datos = {}
    try:
        with open(f'/proc/{pid}/status', 'r') as f:
            for linea in f:
                clave, _, valor = linea.partition(':')
                datos[clave.strip()] = valor.strip()
    except (FileNotFoundError, ProcessLookupError, OSError):
        return None
    return datos


def kb(status, clave):
    """Extrae el número de un valor tipo 'VmRSS: 12345 kB' (ya parseado
    por leer_status, llega como '12345 kB')."""
    valor = status.get(clave)
    if not valor:
        return 0
    try:
        return int(valor.split()[0])
    except (ValueError, IndexError):
        return 0


def clasificar_segmento(linea):
    """Clasifica una línea de /proc/<pid>/maps en heap/stack/lib/text/etc,
    según los permisos y el path del mapeo."""
    partes = linea.split(None, 5)
    perms = partes[1] if len(partes) > 1 else ''
    path = partes[5].strip() if len(partes) > 5 else ''

    if '[heap]' in path:
        return 'heap'
    if '[stack]' in path:
        return 'stack'
    if '.so' in path:
        return 'lib'
    if 'x' in perms and path and not path.startswith('['):
        return 'text'
    if path == '':
        return 'anon'
    return 'data'


def leer_maps_agrupado(pid):
    """Suma el tamaño (KB) de los segmentos de memoria de un proceso,
    agrupados por categoría (heap/stack/lib/text/data/anon)."""
    grupos = {'text': 0, 'data': 0, 'heap': 0, 'stack': 0, 'lib': 0, 'anon': 0}
    try:
        with open(f'/proc/{pid}/maps', 'r') as f:
            for linea in f:
                rango = linea.split()[0]
                inicio_str, fin_str = rango.split('-')
                tam_kb = (int(fin_str, 16) - int(inicio_str, 16)) // 1024
                cat = clasificar_segmento(linea)
                grupos[cat] = grupos.get(cat, 0) + tam_kb
    except (FileNotFoundError, ProcessLookupError, OSError):
        return None
    return grupos


def clasificar_fd(destino):
    """Clasifica el destino de un symlink de /proc/<pid>/fd/<n> según
    a qué apunta: socket, pipe, tty, anon_inode o archivo regular."""
    if destino.startswith('socket:'):
        return 'socket'
    if destino.startswith('pipe:'):
        return 'pipe'
    if destino.startswith('/dev/pts') or destino.startswith('/dev/tty'):
        return 'tty'
    if destino.startswith('anon_inode:'):
        return 'anon_inode'
    return 'file'


def leer_stat_thread(pid, tid):
    """Igual que leer_stat_completo pero para un thread (LWP) puntual,
    vía /proc/<pid>/task/<tid>/stat."""
    try:
        with open(f'/proc/{pid}/task/{tid}/stat', 'r') as f:
            contenido = f.read()
    except (FileNotFoundError, ProcessLookupError, OSError):
        return None
    fin_nombre = contenido.rindex(')')
    resto = contenido[fin_nombre + 1:].split()
    try:
        return {'estado': resto[0], 'utime': int(resto[11]), 'stime': int(resto[12])}
    except (IndexError, ValueError):
        return None


def leer_comm_thread(pid, tid):
    """Nombre del thread desde /proc/<pid>/task/<tid>/comm."""
    try:
        with open(f'/proc/{pid}/task/{tid}/comm', 'r') as f:
            return f.read().strip()
    except (FileNotFoundError, ProcessLookupError, OSError):
        return '?'


def nombre_senal(numero):
    """Convierte un número de señal (ej: 10) a su nombre (ej: SIGUSR1)."""
    try:
        return signal.Signals(numero).name
    except ValueError:
        return f'SIG{numero}'


def decodificar_mascara(hexmask):
    """SigBlk/SigIgn/SigCgt/SigPnd son máscaras hexadecimales de 64 bits
    donde cada bit representa una señal. Esto las decodifica a una
    lista de nombres legibles (SIGTERM, SIGINT, etc)."""
    try:
        valor = int(hexmask, 16)
    except ValueError:
        return []
    nombres = []
    for bit in range(1, 65):
        if valor & (1 << (bit - 1)):
            nombres.append(nombre_senal(bit))
    return nombres


def leer_cpu_global():
    """Primera línea 'cpu ...' de /proc/stat: jiffies acumulados de
    user/nice/system/idle/iowait/irq/softirq/steal/guest/guest_nice."""
    with open('/proc/stat', 'r') as f:
        for linea in f:
            if linea.startswith('cpu '):
                return [int(x) for x in linea.split()[1:]]
    return None


def leer_loadavg():
    with open('/proc/loadavg', 'r') as f:
        p = f.read().split()
        return [float(p[0]), float(p[1]), float(p[2])]


def leer_meminfo():
    datos = {}
    with open('/proc/meminfo', 'r') as f:
        for linea in f:
            clave, _, valor = linea.partition(':')
            try:
                datos[clave.strip()] = int(valor.split()[0])
            except (ValueError, IndexError):
                pass
    return datos


def leer_uptime():
    with open('/proc/uptime', 'r') as f:
        return float(f.read().split()[0])


def leer_btime():
    """Timestamp Unix del momento de boot del sistema, desde la línea
    'btime' de /proc/stat."""
    with open('/proc/stat', 'r') as f:
        for linea in f:
            if linea.startswith('btime'):
                return int(linea.split()[1])
    return None


def leer_usuarios():
    """Parsea /etc/passwd una sola vez: uid -> nombre de usuario.
    No es /proc, pero vive acá porque es otro dato "del sistema"
    que varios módulos necesitan (el filtro por usuario de la TUI)."""
    mapa = {}
    try:
        with open('/etc/passwd', 'r') as f:
            for linea in f:
                partes = linea.strip().split(':')
                if len(partes) >= 3:
                    nombre_usuario, uid = partes[0], partes[2]
                    try:
                        mapa[int(uid)] = nombre_usuario
                    except ValueError:
                        pass
    except OSError:
        pass
    return mapa
