# Clase 14 - Servidores concurrentes

Puerto por defecto **8080**; todos los scripts aceptan `--port N` (el benchmark también acepta `--puerto`).
Para que la carpeta sea autocontenida escribí mi propia versión de los cuatro servidores
(`servidores_eco.py --modo ...`) y del `benchmark.py`; se comportan igual que los de la cátedra.

## Ejercicios → archivos → cómo correrlos

| Ejercicio | Archivo(s) | Terminal 1 (servidor) | Terminal 2 (cliente) |
|---|---|---|---|
| 1.1 / 1.2 Medir estrategias | `servidores_eco.py`, `benchmark.py` | `python3 servidores_eco.py --modo secuencial --lento 1` (y `threads`, `fork`, `pool`) | `python3 benchmark.py --clientes 20` — o todo junto: `bash comandos.sh medir_todos 1 20` / sin lento: `bash comandos.sh medir_todos 0 200` |
| 1.3 Escala | idem | `python3 servidores_eco.py --modo threads --lento 1` | `python3 benchmark.py --clientes 500` — o `bash comandos.sh escala threads` / `escala fork` |
| 2 Pool que satura | idem | `python3 servidores_eco.py --modo pool --workers 5 --lento 1` | `python3 benchmark.py --clientes 20` (o `bash comandos.sh pool 5`, `pool 1`) |
| 3 A / A2 fd del padre | `ej3_server_fork_descuidos.py`, `ej3_gc_fd.py`, `ej3_cliente_espera.py` | `python3 ej3_server_fork_descuidos.py --descuido sin-close` (A) / `--descuido guardar` (A2) | `bash comandos.sh observar_fork <PID>`; `python3 ej3_gc_fd.py`; A2.7: `python3 ej3_cliente_espera.py` + `bash comandos.sh matar_hijo <PID>` |
| 3 B Zombies | `ej3_server_fork_descuidos.py` | `... --descuido sin-handler` | `bash comandos.sh observar_fork <PID>` (correrlo dos veces) |
| 3 C Cosechador sin bucle | `ej3_server_fork_descuidos.py`, `ej3_zombies_simultaneos.py` | `... --descuido sin-bucle` | `bash comandos.sh observar_fork <PID>`; `python3 ej3_zombies_simultaneos.py --repetir 5` y `... --bucle` |
| 3 D SIG_IGN | `ej3_server_fork_descuidos.py` | `... --descuido sig-ign` | `bash comandos.sh observar_fork <PID>` |
| 4 Race conditions | `ej4_threads_race.py` | `python3 ej4_threads_race.py --sin-lock` (luego `--pausa 0.0001`); al final Ctrl+C imprime el contador | `bash comandos.sh carga 200` |
| 5 socketserver | `ej5_socketserver.py` | `python3 ej5_socketserver.py --lento 1` / `--forking` | `python3 benchmark.py --clientes 20` |
| 6 CPU real | `ej6_cpu.py` | `python3 ej6_cpu.py --modo threads` / `--modo fork` | `python3 benchmark.py --clientes 10`; `bash comandos.sh info_cpu` |
| Adic. límite | `ad_limite_conexiones.py` | `python3 ad_limite_conexiones.py --max 5 --lento 1` | `python3 benchmark.py --clientes 12` |
| Adic. STATS | `ad_stats.py` | `python3 ad_stats.py` | `nc localhost 8080` → escribir líneas y `STATS` |
| Adic. cierre ordenado | `ad_cierre_ordenado.py` | `python3 ad_cierre_ordenado.py --lento 2 --gracia 10` → Ctrl+C | `echo hola \| nc -N localhost 8080` |
| Adic. nginx | — | **No hecho** (ver abajo) | |

Ojo: `ad_stats.py` es por líneas, así que el `benchmark.py` (manda 256 bytes sin `\n`) no sirve para él; usar `nc`.

## Qué se probó (Linux, Python 3.13, 2 núcleos, puertos 28100-28199)

Todo lo de la tabla salvo nginx (no estaba instalado ni había `ab`/`wrk`, y el sandbox no tenía salida a
Internet para instalarlo). Los números de abajo son de **esa** máquina; en otra cambian.

## Respuestas

### Ejercicio 1
| Servidor (`--lento 1`, 20 clientes) | Tiempo total | Latencia máx | Throughput |
|---|---|---|---|
| Secuencial | 20,02 s | 20,00 s | 1,0 cl/s |
| Threads | 1,02 s | 1,01 s | 19,6 cl/s |
| Fork | 1,04 s | 1,01 s | 19,3 cl/s |
| Pool (20) | 1,02 s | 1,01 s | 19,7 cl/s |

1. 20 s: lo esperado, 20 clientes × 1 s uno atrás del otro.
2. Mínima 1,0 s (el primero) y máxima 20 s (el último esperó a los 19 anteriores en la cola de `listen`).
3. Latencias escalonadas: la diferencia entre mínima y máxima es mayor que la mitad de la máxima → los atendió en serie.
4. Tabla de arriba.
5. Porque el "trabajo" es un `sleep` (I/O simulado): no usa CPU y todos duermen en paralelo. Con 20 clientes y 20 hilos/procesos/workers nadie espera; el costo de crear hilo o proceso (~ms) es despreciable frente a 1 s.
6. Sin `--lento` (200 clientes): secuencial 0,13 s, threads 0,18 s, fork 0,36 s, pool 0,09 s. Ahora gana el que tiene menos overhead (el pool reutiliza hilos; el fork paga crear un proceso por cliente) y el secuencial hasta le gana a los threads. Sin espera, la concurrencia no aporta y solo suma costo; con espera, es lo único que importa. Por eso el parámetro da vuelta las conclusiones.
7. Threads con `--lento 1`: 50→1,03 s, 100→1,06, 200→1,10, 500→1,26, 1000→1,58 s (todos OK). No se cayó; se degrada levemente desde ~500 por crear tantos hilos a la vez (y el propio benchmark también usa 1000 hilos).
8. Fork: 50→1,07, 100→1,15, 200→1,31, 500→1,77, 1000→2,33 s (todos OK pero degrada antes). Crear un proceso (fork, copiar tabla de páginas, cosechar) es mucho más caro que un hilo, y 1000 procesos ocupan más memoria.
9. `ulimit -n` era 20000, así que no llegué a ese techo. Con 1000 clientes se usan ~1000 fd en el server (más ~1000 en el benchmark, que es otro proceso); antes del límite de fd pesa el costo de crear hilos/procesos y la memoria. Con `ulimit -n 1024` (típico) sí aparecería `OSError: Too many open files` cerca de 1000.

### Ejercicio 2
1. 4,0 s: 20 clientes / 5 workers = 4 tandas de 1 s.
2. Mínima 1,0 s, máxima 4,0 s: 4 escalones (1, 2, 3, 4 s).
3. Ninguno rechazado (20/20 completados). Rechazado = la conexión falla (RST/timeout); demorado = conecta enseguida (lo acepta el kernel/accept) pero espera en la cola del pool a que se libere un worker.
4. `--workers 1`: 20,0 s y latencias 1→20 s, igual que el **secuencial**.
5. Para tareas cortas e independientes (pedido-respuesta corto, tipo HTTP sin keep-alive, o trabajos de CPU en un `ProcessPool` con tantos workers como núcleos). No para conexiones largas o persistentes, que retienen el worker.

### Ejercicio 3 (obligatorio)
Medido con `observar_fork` (2 × 50 clientes):

| `--descuido` | fd del padre antes → después | zombies |
|---|---|---|
| `ninguno` | 4 → 4 | 0 |
| `sin-close` | 4 → 5 | 0 |
| `guardar` | 4 → **104** | 0 |
| `sin-handler` | 4 → 4 | **100** |
| `sin-bucle` | 4 → 4 | **33** |
| `sig-ign` | 4 → 4 | 0 |

**Parte A**
1. No crece (4 → 5: solo queda abierta la última `conn`, que la variable todavía referencia).
2. `ej3_gc_fd.py`: `fd 3 ya está cerrado: Bad file descriptor`. Lo cerró CPython: al salir de `make()` el refcount del socket llega a 0 y `socket.__del__` cierra el fd (ni siquiera hace falta `gc.collect()`).
3. Al reasignar `conn`, el objeto anterior pierde su última referencia, se destruye en ese momento y su fd se cierra.
4. No es innecesario: en **C** `accept()` devuelve un `int` y nadie lo cierra → fuga segura. Si el padre **guarda** las conexiones en una lista, la referencia sobrevive y el fd queda abierto (la parte A2 lo muestra). En **PyPy** (GC diferido, sin refcount) el cierre ocurre "algún día", y mientras tanto se acumulan fd y conexiones colgadas.
5. Porque el cierre por GC es un detalle de implementación de CPython, no una garantía del lenguaje; el `close()` explícito dice exactamente cuándo se libera el recurso, funciona en cualquier intérprete y aguanta que alguien después guarde la referencia.

**Parte A2**
6. Sí: 4 → 104 después de 100 clientes (uno por conexión).
7. No ve el cierre: con `ej3_cliente_espera.py`, al matar al hijo pasaron 3 s y "la conexión sigue abierta (no llegó FIN)". Con el servidor correcto, al matar al hijo el cliente recibe `b''` al instante. (Con `nc` OpenBSD no se nota nada en ninguno de los dos casos, porque no termina mientras su stdin siga abierto; por eso el cliente propio.)
8. Después del `fork()` hay **dos** descriptores (padre e hijo) apuntando al mismo socket del kernel. La conexión TCP solo se cierra (sale el FIN) cuando se cierra la **última** referencia. Si el padre conserva la suya, matar al hijo no cierra nada.

**Parte B**
4. `STAT` = `Z` (zombie, `<defunct>`): terminaron pero nadie hizo `wait()` para leer su estado.
5. 50 después de la primera corrida, 100 después de la segunda: se acumulan.
6. Durante semanas se llena la tabla de procesos (cada zombie ocupa un PID); al llegar al límite (`pid_max` o `ulimit -u`) `fork()` falla con `EAGAIN` y el servidor deja de atender (y a veces otros procesos del usuario tampoco pueden crear procesos).

**Parte C**
7. Con el servidor y el benchmark (50 clientes sin `--lento`) **sí** me quedaron zombies: 33 de 100. Como el benchmark lanza todo junto, varios hijos terminan casi a la vez y sus señales se fusionan.
8. `ej3_zombies_simultaneos.py` sin bucle, varias corridas: `recogidos=47 zombies=13`, `53/7`, `47/13`, `55/6`... cambia cada vez.
9. Con `--bucle`: siempre `recogidos=60 zombies=0`.
10. Las señales estándar no se encolan: es un bit "pendiente". Si llegan 5 `SIGCHLD` antes de que corra el handler, se ve una sola, y el handler sin bucle recoge un único hijo. Cuántas se fusionan depende del scheduler en cada corrida → intermitente.
11. `WNOHANG` hace que `waitpid` vuelva enseguida con `pid=0` si no hay hijos terminados, en vez de bloquearse. Sin él, el handler con bucle se bloquearía esperando a hijos que siguen vivos (atendiendo clientes), y el padre dejaría de hacer `accept()`: el servidor entero se cuelga dentro de un handler de señal.
12. Mirando la cantidad de zombies a lo largo del tiempo (`ps -eo stat | grep -c Z`, monitoreo de procesos/PIDs del servicio) y alarmas cuando crece; reproducirlo con una prueba de carga que haga terminar muchos hijos juntos; y revisando el código: cualquier `waitpid` en un handler sin `while` es sospechoso.

**Parte D**
10. Con `SIG_IGN` no aparecen zombies (0 tras 100 clientes). Los recoge el **kernel**: en Linux, ignorar explícitamente `SIGCHLD` hace que los hijos no queden zombies (se descartan automáticamente al morir). Contra: el padre ya no puede saber el código de salida de los hijos.

### Ejercicio 4
2. Sin lock (sin pausa), 3 × 200 clientes: el contador volvió a 0. La ventana de la carrera es tan chica que el GIL casi nunca cambia de hilo justo ahí.
3. Con `--pausa 0.0001` entre la lectura y la escritura: `clientes_activos al final: 74 (RACE!)` (600 atendidos). Ahí sí.
4. `x += 1` son varias operaciones: leer (LOAD), sumar, escribir (STORE). Si el hilo A lee 5, el GIL pasa a B que también lee 5 y escribe 6, y después A escribe 6, se perdió un incremento (clase 11). El GIL hace atómica cada instrucción de bytecode, no la secuencia.
5. Porque cada hijo es otro proceso con su **propia copia** de la memoria: no hay variable compartida que pisar (y por lo mismo, un contador global en el padre no se entera de nada sin IPC).

### Ejercicio 5
1. `ThreadingTCPServer` con `--lento 1` y 20 clientes: 1,01 s (igual que `server_threads`). Sin lento, 200 clientes: 0,10 s vs 0,11 s de mis threads a mano: prácticamente lo mismo.
2. Resuelven el buffering: con `rfile.readline()` tenés framing por líneas sin escribir el buffer a mano (lo del ej. 3 de la clase 13), y `wfile.write` hace lo que `sendall`.
3. Con `ForkingTCPServer`: con lento da igual (1,04 s); sin lento baja a ~515 cl/s (0,39 s) por el costo del `fork`, igual que mi fork a mano. Además tiene `max_children = 40`: pasado eso, bloquea esperando hijos.
4. `/usr/lib/python3.13/socketserver.py`: `serve_forever()` hace `select` con timeout y llama a `_handle_request_noblock()`, que hace `get_request()` = `self.socket.accept()` y luego `process_request()`. `ThreadingMixIn.process_request` crea un `threading.Thread`; `ForkingMixIn` hace `os.fork()` y cosecha con `waitpid(..., WNOHANG)` en `collect_children()`. Es el mismo esquema que escribimos a mano (con el agregado del `select` para poder hacer `shutdown()`).
5. Para entender qué pasa abajo (cierre de fd en el padre, zombies, locks, saturación del pool) y poder diagnosticarlo cuando falla; además la librería tiene límites (sin asyncio, sin pool acotado de verdad) y uno tiene que saber cuándo no alcanza.

### Ejercicio 6 (`n = 2.000.000`, ~0,17 s por cliente)
1. Threads, 10 clientes: 2,03 s (latencias 0,80→2,03 s). No escala: es ~10 × 0,17 s, como si fuera secuencial.
2. Fork, 10 clientes: 0,88 s (0,80→0,87 s): ~10 × 0,17 / 2 núcleos. Escala con los núcleos.
3. Con GIL, un solo hilo ejecuta bytecode Python a la vez: los hilos se turnan y usan un solo núcleo. Los procesos tienen cada uno su intérprete y su GIL, y corren en paralelo en los 2 núcleos (`nproc` = 2).
4. `con GIL` (Python 3.13 estándar).
5. En un build free-threaded los hilos sí correrían en paralelo y el punto 1 se acercaría al fork (~0,9 s con 2 núcleos). Lo que **no** cambia: el techo sigue siendo la cantidad de núcleos, y los hilos siguen compartiendo memoria (hacen falta locks, un fallo tira todo el proceso), mientras que el fork da aislamiento a costa de más memoria y de crear procesos.

### Adicionales
- **Límite de conexiones** (`--max 5 --lento 1`, 12 clientes): 5 completados y 7 rechazados enseguida (el cliente recibe `ERROR servidor ocupado` o un RST si llegó a mandar datos antes del cierre). Usa un `BoundedSemaphore` con `acquire(blocking=False)`.
- **STATS**: `activos=2 atendidos=30 bytes=15374 uptime=10.8s`. Todos los contadores se modifican y se leen con el mismo lock (la lectura también, para que la foto sea consistente).
- **Cierre ordenado**: con Ctrl+C/SIGTERM deja de aceptar, avisa con un `threading.Event` y espera con `join(timeout)`; probado que un cliente en curso termina bien (`Todos los clientes terminaron`) y que si se pasa la gracia sale igual (`Timeout: 1 cliente(s) no terminaron`).
- **nginx**: no lo hice (no hay nginx/ab/wrk en la máquina y no se podía instalar). Lo esperable: nginx sirviendo un estático da decenas de miles de pedidos/s con un par de workers, porque usa I/O multiplexada (epoll) en vez de un hilo/proceso por cliente; mis servidores Python rondan 1.000-2.000 cl/s sin lento.
