# Clase 3 — Procesos: fundamentos

Todo se corre **desde esta carpeta**, en Linux (usa `/proc`).

| Ejercicio | Archivo(s) | Cómo correrlo |
|---|---|---|
| 1 — Explorar tu propio proceso | `ej1_mi_proceso.py` | `python3 ej1_mi_proceso.py` (opcional: cantidad de líneas de maps, ej. `python3 ej1_mi_proceso.py 30`) |
| 2 — Árbol de procesos | `comandos.sh` (sección Ej. 2), `ej2_jerarquia.py` | `pstree -p $$` · `ps -ef --forest` · `python3 ej2_jerarquia.py` (sube desde tu shell hasta el PID 1) |
| 3 — Memoria virtual | `comandos.sh` (sección Ej. 3), `ej3_mapa_memoria.py` | `python3 -c "import time; time.sleep(60)" & cat /proc/$!/maps` · `python3 ej3_mapa_memoria.py` (o `python3 ej3_mapa_memoria.py <pid>`) |
| 4 — PIDs y reciclado | `comandos.sh` (sección Ej. 4) | `for i in $(seq 1 20); do sh -c 'echo "PID=$$"'; done; cat /proc/sys/kernel/pid_max` |
| Adicional — Procesos por usuario | `ej5_procesos_por_usuario.py` | `python3 ej5_procesos_por_usuario.py` |
| Adicional — Detector de huérfanos | `ej6_detector_huerfanos.py` | `(sleep 120 &)` para fabricar un huérfano y después `python3 ej6_detector_huerfanos.py` |
| Todos los comandos de terminal | `comandos.sh` | `bash comandos.sh` |

Ojo: dentro de `comandos.sh`, `$$` es el PID del bash que ejecuta el script (no tu shell interactiva).
Para ver tu propia shell, pegá los comandos directamente en la terminal.

## Respuestas

**Ej. 1 — Qué se ve:**
- PID y PPID: el PPID es la shell (bash) desde la que lo lanzaste.
- File descriptors: `0`, `1` y `2` (stdin, stdout, stderr) apuntan a la terminal (`/dev/pts/N`) o al archivo/pipe
  si redirigiste; el script abre su propio `.py` a propósito y aparece como fd `3`. El fd que usa `listdir` para leer
  `/proc/<pid>/fd` aparece y desaparece, por eso se ignora el error de `readlink`.
- Maps: primero aparecen las regiones del ejecutable `python3.x` (lectura, `r-xp` código, `rw-p` datos), después
  `[heap]`, después regiones anónimas y librerías `.so`, y arriba de todo `[stack]`, `[vvar]`, `[vdso]`.

**Ej. 2 — Árbol de procesos:**
- **PID 1**: en una distro normal es `systemd` (o `init`); es el primer proceso de espacio de usuario, lo arranca el
  kernel, adopta a los huérfanos y no se puede matar. En un contenedor Docker, PID 1 es el comando del contenedor
  (ej. `bash` o `python`). En la VM donde se probó era un init propio (`process_api`), lo que muestra que "PID 1" es
  simplemente el primer proceso que lanza el kernel.
- **Padre de tu shell**: depende de cómo abriste la terminal: el emulador de terminal (`gnome-terminal-server`,
  `konsole`...), `sshd` si entraste por SSH, `tmux: server`, o `login` en una consola tty.
- **Subiendo la jerarquía**: shell → terminal/sshd → `systemd --user` / sesión → `systemd` (PID 1), cuyo PPID es 0
  (el kernel). En la prueba: `bash (script) → timeout → bash → claude → environment-manager → sh → process_api (PID 1)`.
- Los hilos del kernel (`[kthreadd]` PID 2 y sus hijos `[kworker/...]`) cuelgan de PID 2, no de PID 1.

**Ej. 3 — Segmentos en `/proc/<pid>/maps`:**
- **Text**: la región `r-xp` cuyo archivo es el ejecutable (`/usr/bin/python3.X`): código de máquina, lectura+ejecución, sin escritura.
  Las regiones `r--p` del mismo archivo son headers ELF y datos de solo lectura (rodata, constantes).
- **Data/BSS**: la región `rw-p` del ejecutable (variables globales inicializadas) y la anónima `rw-p` que le sigue (BSS).
- **Heap**: la línea `[heap]`, justo después del ejecutable; crece hacia arriba con `brk`. Python además pide memoria con
  `mmap` (las regiones anónimas `rw-p` sin nombre, en direcciones altas).
- **Stack**: `[stack]`, cerca del tope del espacio de usuario (`7ffc...`); crece hacia abajo.
- **Regiones intermedias**: librerías compartidas (`libc.so.6`, `libm`, `libz`, `libexpat`, `ld-linux`), cada una con
  sus propias partes `r--p` / `r-xp` / `rw-p`; archivos mapeados (locale, `gconv-modules.cache`), regiones anónimas de `mmap`,
  y `[vvar]`/`[vdso]` (páginas del kernel para syscalls rápidas como `gettimeofday`).
- La columna `p` significa privada (copy-on-write) y `s` compartida.

**Ej. 4 — PIDs y reciclado:**
Los PIDs salen consecutivos (en la prueba: 30795, 30796, ..., 30814), porque el kernel asigna el siguiente libre.
Cada `sh -c` es un proceso nuevo con su propio PID. Cuando se llega a `pid_max` (en la máquina de prueba `32768`;
en distros modernas con systemd suele ser `4194304`) el contador vuelve a empezar desde abajo y reusa PIDs de procesos
que ya terminaron (y fueron recolectados por su padre). Por eso un PID solo identifica a un proceso mientras está vivo:
guardar un PID y usarlo mucho después puede apuntar a otro proceso.

**Adicional — Procesos por usuario:** lee el UID real de `/proc/<pid>/status` (línea `Uid:`) y lo traduce con `pwd`.
Si un UID no tiene nombre en `/etc/passwd` (pasa con procesos de contenedores) se muestra el número. Coincide con
`ps -eo user= | sort | uniq -c` (salvo el propio `ps`/script, que existen en un solo caso).

**Adicional — Detector de huérfanos:** lista los procesos con PPID 1 (excluyendo al propio PID 1). Ojo con la
interpretación: no todos son huérfanos "de verdad": los servicios/daemons que lanza systemd directamente también tienen
PPID 1, y los daemons clásicos se hacen huérfanos a propósito (doble fork). Además, si existe un *subreaper*
(`systemd --user`, `tini`, etc.), los huérfanos se los adopta ese proceso en lugar del PID 1. Con `(sleep 120 &)` el
subshell muere enseguida y el `sleep` aparece en la lista (probado).

## Qué se probó

Todo se corrió en Linux con Python 3.13: los cinco scripts y `comandos.sh` completo. Salidas coherentes con lo esperado
(fds, segmentos del maps, cadena de ancestros hasta PID 1, PIDs consecutivos, conteo por usuario igual a `ps`, el `sleep`
huérfano detectado con PPID 1).
