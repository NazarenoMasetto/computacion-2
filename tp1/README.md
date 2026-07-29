# TP Nº1 — Monitor de Procesos y Threads

**Computación II — Universidad de Mendoza — 2026**

Monitor de sistema en tiempo real, estilo `htop`, que lee `/proc` directamente
(sin `psutil`) y expone 7 vistas alternables sobre el estado de los procesos
del sistema. Está construido como un sistema **multiproceso**: 7 analizadores
independientes corren en paralelo, cada uno con su propio intervalo de
refresco, escribiendo a un snapshot compartido que la interfaz (TUI) lee y
muestra.

---

## 1. Descripción general

El monitor arranca 7 procesos analizadores (Resumen, Memoria, File
Descriptors, Threads, Señales, Scheduling, Sistema), cada uno leyendo una
dimensión distinta de `/proc/<pid>/...` a su propio ritmo. Todos escriben a
un diccionario compartido (`multiprocessing.Manager().dict()`), que el
proceso principal lee para dibujar la vista activa con `rich`.

### Cómo se usa

Con el monitor corriendo, se navega así:

| Tecla | Acción |
|---|---|
| `1-7` / `r m f t s p g` | Cambiar de vista |
| `↑` / `↓` | Navegar por la lista de procesos |
| `Enter` | Pin del proceso seleccionado |
| `/` | Filtrar por nombre de comando |
| `u` | Filtrar por usuario (nombre o UID) |
| `c` | Ciclar orden: CPU% → RSS → PID |
| `+` / `-` | Ajustar el intervalo de refresco de la vista activa |
| `h` / `?` | Ayuda |
| `q` | Salir |

El monitor también responde a señales externas (`kill -SEÑAL <pid>`):
`SIGINT`/`SIGTERM` (shutdown limpio), `SIGHUP` (recarga `config.json`),
`SIGUSR1` (dump del snapshot a JSON), `SIGUSR2` (toggle verbose), `SIGWINCH`
(repintar).

---

## 2. Diagrama de arquitectura

```
                    ┌───────────────────────────────────────┐
                    │         SNAPSHOT GLOBAL                │
                    │    (multiprocessing.Manager().dict())  │
                    │  resumen | memoria | fds | threads |   │
                    │  senales | scheduling | sistema        │
                    └───────────▲─────────────────────▲──────┘
                     escriben   │                      │ lee
          ┌──────────┬─────────┼──────────┬───────────┘
          │          │         │          │
    ┌─────▼────┐┌────▼────┐┌───▼────┐┌────▼─────┐   ...(7 en total,
    │ Resumen  ││ Memoria ││  FDs   ││ Threads  │    cada uno Process
    │ 2s       ││ 3s      ││ 5s     ││ 2s       │    independiente)
    └──────────┘└─────────┘└────────┘└──────────┘
          │          │         │          │
          └──────────┴─────────┴──────────┘
               todos llaman a recolector.listar_pids()
               y funciones de procfs.py para parsear /proc

    ┌─────────────────────────────────────────────────────┐
    │  PROCESO PRINCIPAL (main.py)                        │
    │  - Un solo select() escucha: teclado + pipe señales  │
    │  - display.render() arma la vista con rich.Live      │
    │  - manejador_senales.py procesa SIGINT/HUP/USR1/2/   │
    │    WINCH vía self-pipe (signal.set_wakeup_fd)        │
    └───────────────────────────────────────────────────────┘
```

### Estructura del repo

```
src/
├── main.py                    # orquesta: arranca procesos, loop principal
├── recolector.py               # lista PIDs activos (os.listdir('/proc'))
├── procfs.py                   # helpers puros de lectura/parseo de /proc
├── display.py                  # TUI: tablas, filtros, orden, render()
├── manejador_senales.py         # config.json, dump, self-pipe de señales
└── analizadores/
    ├── resumen.py
    ├── memoria.py
    ├── fds.py
    ├── threads.py
    ├── senales_proceso.py       # señales de OTROS procesos (no del monitor)
    ├── scheduling.py
    └── sistema.py
```

---

## 3. Decisiones de diseño

### ¿Por qué `Manager().dict()` para el snapshot y no `Value`/`Array`?

`Value` y `Array` de `multiprocessing` están pensados para tipos **simples y
de tamaño fijo** (un float, un int, un array homogéneo de tamaño conocido de
antemano). El snapshot de este TP necesita guardar estructuras **anidadas y
de tamaño variable**: listas de diccionarios donde cada proceso puede tener
una cantidad distinta de threads, FDs o segmentos de memoria. `Manager().dict()`
sí soporta esto, porque internamente serializa (pickle) cualquier objeto
Python y lo envía a un proceso servidor dedicado que arbitra el acceso.

Sí usamos `Value` para los **intervalos** de cada analizador (`resumen`,
`memoria`, etc.), porque ahí el dato es un único float de tamaño fijo — el
caso exacto para el que `Value` está diseñado. Esto además nos permite
cambiar el intervalo **en caliente** (con `+`/`-` desde la TUI, o al recargar
`config.json` con `SIGHUP`) sin reiniciar el proceso analizador.

### ¿Cómo se evitan las race conditions?

Cada uno de los 7 analizadores escribe **solo su propia clave** del
diccionario compartido (`snapshot['resumen']`, `snapshot['memoria']`, etc.) —
nunca dos procesos escriben la misma clave al mismo tiempo. Además,
`Manager().dict()` es un *proxy*: cada operación de lectura/escritura viaja
por IPC hacia el proceso servidor del `Manager`, que serializa el acceso
internamente. Esto significa que no hace falta un `Lock` explícito para este
diccionario: la sincronización ya está resuelta por el diseño (una clave por
escritor) más el arbitraje interno del `Manager`.

El único lugar donde sí hay estado mutable compartido entre threads (no
procesos) es dentro de `display.py`/`main.py`, con `estado_ui` y
`estado_senales` — pero esos viven **únicamente en el proceso principal**, no
se comparten con los analizadores, así que no necesitan `Lock`.

### Por qué no hay un proceso Agregador separado

El diagrama del enunciado también sugiere un componente "Agregador" que
recibe datos de los analizadores (por ejemplo vía `Queue`) y los escribe al
snapshot compartido. En esta implementación, cada analizador escribe
**directamente** su propia clave del `Manager().dict()` compartido, sin pasar
por un proceso intermedio. Es la misma lógica de simplificación que con el
Recolector: como cada analizador es dueño exclusivo de su propia clave del
diccionario (nadie más escribe `snapshot['memoria']` salvo el analizador de
Memoria), no hay beneficio real en sumar un Agregador que reciba por `Queue`
y reescriba al mismo dict — solo agregaría un salto más de IPC sin resolver
ningún problema de concurrencia que no estuviera ya resuelto por el diseño
de "una clave por escritor" + el arbitraje interno del `Manager`.

### Por qué el Recolector no es un proceso separado con `Queue`

El diagrama sugerido en el enunciado muestra un Recolector que reparte
trabajo a los analizadores por `Queue`. Decidimos que cada analizador llame
directamente a `recolector.listar_pids()` al inicio de cada uno de sus
propios ciclos, en lugar de tener un proceso Recolector separado coordinando
el reparto. Con un sistema de escritorio típico (unos pocos cientos de PIDs),
el costo de listar `/proc` es despreciable comparado con la complejidad de
coordinar un patrón productor/consumidor de 8 procesos (1 productor + 7
consumidores) sin beneficio real de performance a esta escala. Es una
simplificación consciente, documentada acá.

### Intervalos por defecto elegidos

| Vista | Intervalo default | Motivo |
|---|---|---|
| Resumen, Threads, Sistema | 2s | Datos que cambian rápido (CPU%, estado) |
| Memoria | 3s | Cambia más lento que CPU, pero conviene verlo fresco |
| FDs | 5s | Costoso de leer (un `readlink` por FD abierto) y cambia poco |
| Señales, Scheduling | 10s | Prácticamente estáticos salvo cambios explícitos |

### Bug real: modo `raw` vs `cbreak` en la terminal

Durante el desarrollo de la captura de teclado, usar `tty.setraw()` dejaba la
terminal en un estado donde ni siquiera `Ctrl+C` funcionaba (el modo *raw*
desactiva la generación de señales). Esto causó una sesión de terminal
"trabada" real. La solución fue usar `tty.setcbreak()` en su lugar, que
deshabilita el buffering por línea (necesario para leer teclas sin Enter)
pero preserva la generación de señales del terminal.

### Bug real: contenido desbordando la terminal

Al principio usamos `Live(..., screen=False)`, que solo repinta agregando
líneas nuevas. Con tablas más largas que la altura real de la terminal, el
panel de estado (con la info de señales/filtros) quedaba empujado fuera de
la vista, dando la falsa impresión de que las señales no llegaban. La
solución fue pasar a `screen=True` (modo pantalla alternativa, como `htop`),
que hace que `rich` conozca el tamaño real de la terminal y recorte el
contenido en vez de desbordarlo.

### Bug real: `pid: host` y el significado de "PID 1"

Al intentar mandar señales con `docker kill --signal=USR2 <contenedor>` o
`kill -USR2 1` dentro del contenedor, la señal llegaba al proceso equivocado
(`systemd` del host). Esto pasa porque `pid: host` en el compose hace que el
contenedor **comparta el namespace de PID del host** — el proceso del monitor
no tiene un PID "1" propio dentro de un namespace aislado, sino su PID real
del sistema. La solución fue obtener el PID real con
`docker inspect --format '{{.State.Pid}}' <contenedor>` y mandar la señal
directo a ese PID.

---

## 4. Conceptos del curso aplicados

- **Zombies (Clase 4 — fork/exec/wait)**: en la vista Sistema, un proceso
  zombie se detecta por el campo `State` de `/proc/<pid>/stat` siendo `Z` —
  es un proceso que terminó pero cuyo padre todavía no llamó a `wait()`.

- **Namespaces de PID (Clase 3/8)**: el flag `pid: host` del
  `docker-compose.yml` hace que el contenedor comparta el namespace de PIDs
  del sistema real en vez de tener el suyo propio aislado — sin esto, el
  monitor solo vería 1-2 procesos (los del propio contenedor).

- **fork() y Copy-on-Write (Clase 4)**: `multiprocessing.Process` en Linux
  usa `fork()` por debajo. Gracias a COW, arrancar 7 procesos analizadores no
  duplica físicamente la memoria del proceso padre — las páginas se comparten
  hasta que alguno las modifica.

- **jiffies y cálculo de %CPU (Clase 3)**: los campos 14 y 15 de
  `/proc/<pid>/stat` (`utime`, `stime`) son contadores acumulados de jiffies
  de CPU, no un porcentaje. Para calcular %CPU hace falta comparar **dos**
  lecturas separadas en el tiempo: `(Δjiffies / HZ) / Δtiempo_real * 100`.
  Por eso cada analizador de CPU guarda un diccionario `anterior` con la
  lectura previa.

- **Threads como LWPs (Clase 10)**: cada archivo en
  `/proc/<pid>/task/<tid>/` representa un thread (Light-Weight Process) del
  proceso `<pid>`. El analizador de Threads lista `/proc/<pid>/task` para
  encontrar todos los TIDs de cada proceso.

- **GIL y por qué multiproceso (Clase 10)**: aunque leer archivos de `/proc`
  es I/O-bound (donde el GIL no sería tan limitante con threads), el
  enunciado exige arquitectura multiproceso explícitamente, y además nos da
  aislamiento real: si un analizador se cuelga o crashea, no afecta a los
  demás ni al proceso principal (cosa que si fueran threads del mismo
  proceso, un error no controlado podría afectar el intérprete completo).

- **Señales y async-signal-safe (Clase 6)**: los handlers de señal del
  monitor (`manejador_noop`) no hacen ningún trabajo — el patrón **self-pipe**
  (`signal.set_wakeup_fd`) hace que el propio sistema operativo escriba 1
  byte a un pipe cuando llega una señal, y todo el procesamiento real ocurre
  en el loop principal, cuando `select()` detecta que el pipe tiene datos.
  Esto es necesario porque hacer operaciones complejas (leer archivos,
  escribir JSON) directo dentro de un handler de señal puede causar
  condiciones de carrera o deadlocks si la señal interrumpe al proceso en un
  punto delicado.

- **Race conditions y sincronización (Clase 9)**: ver sección de decisiones
  de diseño más arriba — la elección de una clave por escritor en el
  `Manager().dict()` evita la necesidad de un `Lock` explícito.

---

## 5. Limitaciones conocidas

- El "Recolector" del diagrama no es un proceso `Process` separado con
  `Queue` propia, sino una función (`recolector.listar_pids()`) que cada
  analizador llama directamente. Del mismo modo, tampoco hay un proceso
  "Agregador" separado: cada analizador escribe directo su propia clave del
  snapshot compartido. Ver justificación de ambas simplificaciones en
  Decisiones de diseño.
- La navegación con `↑`/`↓` selecciona por **índice visible** dentro de la
  lista ya filtrada/ordenada, no por PID — si la lista se reordena entre un
  refresco y otro (por ejemplo, cambia el top de CPU), la selección puede
  "saltar" a otro proceso. El pin (`Enter`) sí es por PID y no tiene este
  problema.
- El filtro por comando/usuario depende de que el analizador de Resumen ya
  tenga al menos una lectura hecha (usamos sus datos como tabla de
  referencia cruzada de PID→nombre/UID para las demás vistas). En el primer
  segundo tras arrancar, el filtro puede no encontrar coincidencias.
- `docker-compose.yml` requiere `pid: host` y `privileged: true` para poder
  leer `/proc` de todos los procesos del sistema real — esto reduce el
  aislamiento normal de un contenedor Docker, un trade-off necesario para
  que el monitor cumpla su función.
- `decodificar_mascara()` recorre los 64 bits de las máscaras de señales en
  Python puro en cada refresco. No es un cuello de botella a los intervalos
  usados (5-10s para la vista de Señales), pero no está optimizado con una
  tabla de lookup precomputada.
- Cada analizador recorre secuencialmente todos los PIDs en cada ciclo (sin
  paralelizar la lectura interna). Es aceptable para la escala de un sistema
  de escritorio (cientos de procesos), pero no escalaría bien a sistemas con
  decenas de miles de procesos.

---

## 6. Cómo correr y testear

### Requisitos
- Docker y Docker Compose

### Levantar el monitor

```bash
docker compose up --build -d
docker attach tp1-monitor-1
```

> Importante: usar `up -d` + `attach`, **no** `docker compose up` a secas —
> en algunas versiones de Docker Compose, correrlo sin `-d` no reenvía bien
> el teclado al contenedor.

Para salir del monitor: tecla `q` (o `Ctrl+C` como salida de emergencia).
Salir de la consola sin apagar el contenedor: no aplica acá, `q` apaga el
monitor y el contenedor junto con él.

### Probar las señales

```bash
# Conseguir el PID real del proceso (pid: host => el PID del contenedor
# ES el PID real del sistema, no un PID de namespace aislado)
docker inspect --format '{{.State.Pid}}' tp1-monitor-1

# Mandar una señal (puede requerir sudo si el proceso corre como root
# dentro del contenedor)
sudo kill -USR1 <PID>   # dump del snapshot a dump_<timestamp>.json
sudo kill -USR2 <PID>   # toggle verbose
sudo kill -HUP  <PID>   # recarga config.json
sudo kill -WINCH <PID>  # repinta
```

### Editar `config.json`

Vive en la raíz del repo (no en `src/`). Permite ajustar los intervalos por
vista y los filtros default, y se puede recargar en caliente con `SIGHUP`
sin reiniciar el monitor:

```json
{
  "intervalos": { "resumen": 2.0, "memoria": 3.0, ... },
  "filtros": { "comando": "", "uid": null }
}
```

---

## 7. Decisiones sobre la TUI

Se usó la librería `rich` (en vez de `curses`) por su soporte directo de
tablas con estilos (`rich.table.Table`), paneles (`rich.panel.Panel`), y el
modo de refresco en vivo `rich.live.Live` con `screen=True` (pantalla
alternativa, igual que usa `htop` o `vim`). Esto evita tener que manejar
manualmente el posicionamiento de cursor y el borrado de pantalla que
requeriría `curses` para un resultado equivalente.

La entrada de teclado se resuelve con un único `select()` que escucha tanto
el file descriptor de `stdin` como el pipe de señales (self-pipe) — esto
evita necesitar un thread separado para el teclado (el enunciado lo permite
pero no lo exige), simplificando la concurrencia del proceso principal a un
solo flujo de control.

---

## 8. Lo que aprendí

*(Esta sección la completa el autor con su reflexión personal — no la
generamos automáticamente porque se supone que refleja el propio proceso de
aprendizaje, y es exactamente lo que se evalúa en la defensa oral.)*

Algunas preguntas guía para escribir 2-3 párrafos propios:

- ¿Qué fue lo que más te costó entender conceptualmente de todo el TP?
- De los bugs reales que documentamos arriba (modo raw/cbreak, pantalla
  desbordada, `pid: host` y PID 1), ¿cuál te enseñó algo que no sabías antes,
  y qué fue exactamente?
- ¿Hay algo que hiciste "porque funcionó" pero todavía no podés explicar del
  todo por qué? (Vale la pena anotarlo en `dudas.md` — el enunciado dice que
  la honestidad intelectual no penaliza.)
- Si tuvieras que rehacer este TP de cero, ¿qué cambiarías de la
  arquitectura?

---

*Trabajo Práctico Nº 1 — Computación II — 2026*
