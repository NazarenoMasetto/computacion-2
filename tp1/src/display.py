"""
display.py

Todo lo relacionado a "qué se dibuja en pantalla": las 7 vistas, sus
tablas, los filtros por comando/usuario, el orden, y el resaltado de
selección/pin. main.py se encarga del *loop* y del teclado; este
módulo solo construye lo que hay que mostrar dado un estado.
"""

import time
from rich.table import Table
from rich.panel import Panel
from rich.console import Group

VISTAS = {
    '1': 'resumen', 'r': 'resumen',
    '2': 'memoria', 'm': 'memoria',
    '3': 'fds', 'f': 'fds',
    '4': 'threads', 't': 'threads',
    '5': 'senales', 's': 'senales',
    '6': 'scheduling', 'p': 'scheduling',
    '7': 'sistema', 'g': 'sistema',
}


# ============================================================
# FILTROS Y ORDEN (se aplican antes de dibujar cualquier tabla)
# ============================================================

def construir_mapa_pid(snapshot):
    """El analizador de Resumen es el único que tiene nombre+uid juntos
    por PID. Lo usamos como referencia cruzada para poder filtrar por
    comando/usuario en CUALQUIER vista (fds, threads, señales, etc.),
    aunque esa vista puntual no traiga esos campos."""
    mapa = {}
    entrada = snapshot.get('resumen')
    if entrada:
        for p in entrada['data']:
            mapa[p['pid']] = {'nombre': p['nombre'], 'uid': p['uid']}
    return mapa


def aplicar_filtros(datos, mapa_pid, filtro_comando, filtro_uid):
    """Filtra una lista de dicts (todas tienen 'pid') según nombre de
    comando (substring, case-insensitive) y/o UID exacto."""
    if not filtro_comando and filtro_uid is None:
        return datos
    salida = []
    for item in datos:
        info = mapa_pid.get(item['pid'])
        if not info:
            continue
        if filtro_comando and filtro_comando.lower() not in info['nombre'].lower():
            continue
        if filtro_uid is not None and info['uid'] != filtro_uid:
            continue
        salida.append(item)
    return salida


def ordenar(datos, orden, clave_default='pid'):
    """orden: 'cpu' (por cpu_pct desc), 'rss' (por vmrss desc), 'pid' (asc).
    Si el campo pedido no existe en estos datos, cae a PID."""
    if orden == 'cpu' and datos and 'cpu_pct' in datos[0]:
        return sorted(datos, key=lambda x: -x['cpu_pct'])
    if orden == 'rss' and datos and 'vmrss' in datos[0]:
        return sorted(datos, key=lambda x: -x['vmrss'])
    return sorted(datos, key=lambda x: x.get(clave_default, 0))


# ============================================================
# TABLAS: una función por vista
# ============================================================

def _estilo_fila(indice, seleccion):
    return "on grey35" if indice == seleccion else None


def _marca(pid, pin_pid):
    return "📌" if pid == pin_pid else "  "


def tabla_resumen(datos, limite=20, seleccion=None, pin_pid=None):
    t = Table(title="RESUMEN")
    t.add_column("")
    for c in ["PID", "PPID", "UID", "THR", "CPU%", "ESTADO", "NOMBRE"]:
        t.add_column(c, justify="right" if c not in ("NOMBRE", "ESTADO") else "left")
    for i, p in enumerate(datos[:limite]):
        t.add_row(_marca(p['pid'], pin_pid), str(p['pid']), str(p['ppid']), str(p['uid']),
                   str(p['threads']), str(p['cpu_pct']), p['estado'], p['nombre'],
                   style=_estilo_fila(i, seleccion))
    return t


def tabla_memoria(datos, limite=20, seleccion=None, pin_pid=None):
    t = Table(title="MEMORIA")
    t.add_column("")
    for c in ["PID", "NOMBRE", "VmRSS(KB)", "VmSize(KB)", "Swap(KB)", "MinFlt", "MajFlt"]:
        t.add_column(c, justify="right" if c not in ("NOMBRE",) else "left")
    for i, p in enumerate(datos[:limite]):
        t.add_row(_marca(p['pid'], pin_pid), str(p['pid']), p['nombre'], str(p['vmrss']),
                   str(p['vmsize']), str(p['vmswap']), str(p['minflt']), str(p['majflt']),
                   style=_estilo_fila(i, seleccion))
    return t


def tabla_fds(datos, limite=20, seleccion=None, pin_pid=None):
    t = Table(title=f"FILE DESCRIPTORS (top {limite} por cantidad)")
    t.add_column("")
    t.add_column("PID", justify="right")
    t.add_column("Cantidad FDs", justify="right")
    for i, p in enumerate(datos[:limite]):
        t.add_row(_marca(p['pid'], pin_pid), str(p['pid']), str(p['cantidad']),
                   style=_estilo_fila(i, seleccion))
    return t


def tabla_threads(datos, limite=15, seleccion=None, pin_pid=None):
    t = Table(title=f"THREADS (top {limite} procesos con más threads)")
    t.add_column("")
    t.add_column("PID", justify="right")
    t.add_column("Cant. Threads", justify="right")
    t.add_column("TIDs (muestra)")
    for i, p in enumerate(datos[:limite]):
        muestra = ", ".join(str(th['tid']) for th in p['threads'][:5])
        t.add_row(_marca(p['pid'], pin_pid), str(p['pid']), str(len(p['threads'])), muestra,
                   style=_estilo_fila(i, seleccion))
    return t


def tabla_senales(datos, limite=20, seleccion=None, pin_pid=None):
    t = Table(title="SEÑALES (procesos con handlers propios)")
    t.add_column("")
    t.add_column("PID", justify="right")
    t.add_column("Con handler (SigCgt)")
    con_handler = [p for p in datos if p['con_handler']]
    for i, p in enumerate(con_handler[:limite]):
        t.add_row(_marca(p['pid'], pin_pid), str(p['pid']), ", ".join(p['con_handler'][:6]),
                   style=_estilo_fila(i, seleccion))
    return t


def tabla_scheduling(datos, limite=20, seleccion=None, pin_pid=None):
    t = Table(title="SCHEDULING")
    t.add_column("")
    for c in ["PID", "NOMBRE", "NICE", "POLICY", "AFFINITY", "VolCtx", "NonVolCtx"]:
        t.add_column(c, justify="right" if c not in ("NOMBRE", "POLICY", "AFFINITY") else "left")
    for i, p in enumerate(datos[:limite]):
        t.add_row(_marca(p['pid'], pin_pid), str(p['pid']), p['nombre'], str(p['nice']),
                   p['policy'], p['affinity'], p['vol_ctxt'], p['nonvol_ctxt'],
                   style=_estilo_fila(i, seleccion))
    return t


def _top3(datos, clave, limite=3):
    """Top N de una lista de dicts, ordenados desc por 'clave'. Usado
    para derivar 'Top 3 por CPU y por memoria' de la vista Sistema,
    cruzando los datos que YA recolectaron los analizadores de
    Resumen y Memoria -- no releemos /proc de nuevo."""
    return sorted(datos, key=lambda x: -x.get(clave, 0))[:limite]


def panel_sistema(datos, top3_cpu, top3_mem):
    s = datos

    if s.get('btime'):
        boot_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(s['btime']))
    else:
        boot_str = '?'

    lineas_top_cpu = "\n".join(
        f"    {p['pid']:>7}  {p['cpu_pct']:>5}%  {p['nombre']}" for p in top3_cpu
    ) or "    (sin datos todavía)"

    lineas_top_mem = "\n".join(
        f"    {p['pid']:>7}  {p['vmrss']:>8}KB  {p['nombre']}" for p in top3_mem
    ) or "    (sin datos todavía)"

    texto = (
        f"CPU:  user={s['cpu_pct']['user']}%  system={s['cpu_pct']['system']}%  "
        f"idle={s['cpu_pct']['idle']}%  iowait={s['cpu_pct']['iowait']}%\n"
        f"Load average: {s['load']}\n"
        f"Memoria: total={s['mem_total_kb']}KB  libre={s['mem_free_kb']}KB  "
        f"buffers={s['mem_buffers_kb']}KB  cache={s['mem_cached_kb']}KB\n"
        f"Swap: total={s['swap_total_kb']}KB  libre={s['swap_free_kb']}KB\n"
        f"Procesos: {s['total_procesos']}  Zombies: {s['zombies']}  "
        f"Threads totales: {s['threads_totales']}\n"
        f"Boot time: {boot_str}   |   Uptime: {round(s['uptime_seg'] / 3600, 1)} horas\n\n"
        f"Top 3 por CPU%:\n{lineas_top_cpu}\n\n"
        f"Top 3 por Memoria (RSS):\n{lineas_top_mem}"
    )
    return Panel(texto, title="SISTEMA")


TABLAS_POR_VISTA = {
    'resumen': tabla_resumen, 'memoria': tabla_memoria, 'fds': tabla_fds,
    'threads': tabla_threads, 'senales': tabla_senales, 'scheduling': tabla_scheduling,
}


# ============================================================
# RENDER: arma todo lo que hay que mostrar para el estado actual
# ============================================================

def panel_ayuda_completa():
    """Pantalla completa de ayuda (tecla h/?), con las 7 vistas y todos
    los keybindings -- requisito explícito del enunciado."""
    texto = (
        "[bold]VISTAS[/bold]\n"
        "  1 / r  Resumen       (estado, CPU%, RSS, threads, comando)\n"
        "  2 / m  Memoria       (segmentos, faults, swap)\n"
        "  3 / f  File Descriptors (FDs abiertos y sus destinos)\n"
        "  4 / t  Threads       (LWPs con CPU% y estado)\n"
        "  5 / s  Señales       (bloqueadas, ignoradas, con handler, pendientes)\n"
        "  6 / p  Scheduling    (nice, priority, policy, affinity, ctx switches)\n"
        "  7 / g  Sistema global (CPU, memoria, load, totales)\n\n"
        "[bold]NAVEGACIÓN Y ACCIONES[/bold]\n"
        "  ↑ / ↓     Navegar por la lista de procesos\n"
        "  Enter     Pin del proceso seleccionado (no se mueve aunque cambie el orden)\n"
        "  /         Filtrar por nombre de comando\n"
        "  u         Filtrar por usuario (nombre o UID)\n"
        "  c         Ciclar orden: CPU% -> RSS -> PID -> CPU%...\n"
        "  + / -     Ajustar el intervalo de refresco de la vista activa\n"
        "  q         Salir limpiamente\n"
        "  h / ?     Esta ayuda (cualquier tecla la cierra)\n\n"
        "[bold]SEÑALES DEL MONITOR (mandalas con 'kill -SEÑAL <pid>')[/bold]\n"
        "  SIGINT / SIGTERM   Shutdown limpio\n"
        "  SIGHUP             Recarga config.json (intervalos y filtros default)\n"
        "  SIGUSR1            Dump del snapshot a dump_<timestamp>.json\n"
        "  SIGUSR2            Toggle de modo verbose\n"
        "  SIGWINCH           Repintar (terminal redimensionada)\n"
    )
    return Panel(texto, title="AYUDA")


def render(snapshot, vista_actual, estado_senales, estado_ui, intervalo_actual):
    if estado_ui.get('ayuda_visible'):
        contenido = panel_ayuda_completa()
        ayuda = Panel("[bold]h[/bold] / [bold]?[/bold] o cualquier tecla: volver", style="dim")
        return Group(contenido, ayuda)

    entrada = snapshot.get(vista_actual)
    limite = 25 if estado_senales['verbose'] else 12

    if not entrada:
        contenido = Panel(f"Esperando datos de '{vista_actual}'...", title=vista_actual.upper())
        estado_ui['pids_visibles'] = []
    elif vista_actual == 'sistema':
        entrada_resumen = snapshot.get('resumen')
        entrada_memoria = snapshot.get('memoria')
        top3_cpu = _top3(entrada_resumen['data'], 'cpu_pct') if entrada_resumen else []
        top3_mem = _top3(entrada_memoria['data'], 'vmrss') if entrada_memoria else []
        contenido = panel_sistema(entrada['data'], top3_cpu, top3_mem)
        estado_ui['pids_visibles'] = []
    elif vista_actual in TABLAS_POR_VISTA:
        mapa_pid = construir_mapa_pid(snapshot)
        datos = aplicar_filtros(entrada['data'], mapa_pid,
                                 estado_ui['filtro_comando'], estado_ui['filtro_uid'])
        datos = ordenar(datos, estado_ui['orden'])

        cantidad_mostrada = min(len(datos), limite)
        if cantidad_mostrada == 0:
            estado_ui['seleccion'] = 0
        else:
            estado_ui['seleccion'] = max(0, min(estado_ui['seleccion'], cantidad_mostrada - 1))

        constructor = TABLAS_POR_VISTA[vista_actual]
        contenido = constructor(datos, limite, estado_ui['seleccion'], estado_ui['pin_pid'])
        estado_ui['pids_visibles'] = [p['pid'] for p in datos[:limite]]
    else:
        contenido = Panel("Vista desconocida")
        estado_ui['pids_visibles'] = []

    verbose_txt = "ON" if estado_senales['verbose'] else "OFF"
    ultima = estado_senales['ultima_senal'] or "-"
    ultimo_dump = estado_senales.get('ultimo_dump') or "-"
    ayuda = Panel(
        "[bold]1-7[/bold] vista  [bold]↑↓[/bold] navegar  [bold]Enter[/bold] pin  "
        "[bold]/[/bold] filtro cmd  [bold]u[/bold] filtro user  [bold]c[/bold] sort  "
        "[bold]+/-[/bold] intervalo  [bold]h/?[/bold] ayuda  [bold]q[/bold] salir   |   "
        f"verbose:{verbose_txt}  señal:{ultima}  dump:{ultimo_dump}  "
        f"intervalo({vista_actual}):{intervalo_actual}s",
        style="dim",
    )

    filtro_txt = (
        f"orden: {estado_ui['orden']}   |   "
        f"filtro comando: '{estado_ui['filtro_comando']}'   |   "
        f"filtro uid: {estado_ui['filtro_uid'] if estado_ui['filtro_uid'] is not None else '-'}   |   "
        f"pin: {estado_ui['pin_pid'] or '-'}"
    )
    if estado_ui['modo_input']:
        etiqueta = "Comando" if estado_ui['modo_input'] == 'comando' else "Usuario"
        filtro_txt = f"[bold yellow]Escribiendo filtro por {etiqueta}: {estado_ui['buffer_input']}_[/bold yellow]"

    panel_filtros = Panel(filtro_txt, style="dim")
    return Group(contenido, ayuda, panel_filtros)
