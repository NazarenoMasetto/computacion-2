# Clase 06 - Señales

Todo en Python 3 (stdlib), probado en Linux con Python 3.13.
Para los programas que esperan señales: correlos en una terminal, copiá el PID que imprimen
y mandá las señales desde **otra terminal** con `kill`.

| Ejercicio | Archivo(s) | Cómo correrlo |
|---|---|---|
| 1.1 / 1.2 / 1.3 Señales desde la terminal | `comandos.sh` | `bash comandos.sh` (lanza sus propios `sleep`/`python3` y solo les manda señales a ellos) |
| 2.1 Capturar Ctrl+C | `ej2_1_ctrl_c.py` | `python3 ej2_1_ctrl_c.py` y apretar Ctrl+C 3 veces (o desde otra terminal: `kill -INT <pid>` x3, el PID se ve con `pgrep -f ej2_1`) |
| 2.2 Shutdown limpio con SIGTERM | `ej2_2_sigterm_shutdown.py` | `python3 ej2_2_sigterm_shutdown.py` → otra terminal: `kill <pid>` |
| 3.1 Padre → hijo con SIGUSR1/SIGUSR2 | `ej3_1_padre_hijo_usr.py` | `python3 ej3_1_padre_hijo_usr.py` (se manda las señales solo) |
| 3.2 SIGCHLD | `ej3_2_sigchld.py` | `python3 ej3_2_sigchld.py` |
| 4.1 Timeout con SIGALRM | `ej4_1_timeout.py` | `python3 ej4_1_timeout.py` |
| 4.2 Timer periódico (setitimer) | `ej4_2_timer_periodico.py` | `python3 ej4_2_timer_periodico.py` (Ctrl+C corta antes) |
| 5 Servidor con señales (obligatorio) | `servidor_signals.py` | `python3 servidor_signals.py` → otra terminal: `kill -USR1 <pid>`, `kill -HUP <pid>`, `kill -USR2 <pid>`, `kill <pid>` |
| 6.1 Pool de workers supervisado | `ej6_pool_workers.py` | `python3 ej6_pool_workers.py [n_workers]` → terminar con Ctrl+C o `kill <pid_supervisor>` |
| Adicional: Watchdog | `adicional_watchdog.py` | `python3 adicional_watchdog.py` (worker de prueba que falla al azar) o `python3 adicional_watchdog.py -- sleep 30` → simular caída: `kill -9 <pid_hijo>` (`pgrep -P <pid_watchdog>`); terminar: `kill <pid_watchdog>` |
| Adicional: Rate limiter | `adicional_rate_limiter.py` | `python3 adicional_rate_limiter.py [N] [segundos]` (ej: `python3 adicional_rate_limiter.py 4 3`) |
| Adicional: Señales como comandos | `adicional_senales_comandos.py` | `python3 adicional_senales_comandos.py` → otra terminal: 1 USR1 = stats: `kill -USR1 <pid>`; 2 USR1 = reset: `kill -USR1 <pid>; sleep 0.1; kill -USR1 <pid>`; 3 USR1 = pausa/reanudar (igual, con 3) |

Notas de implementación:
- Los servidores usan `sys.stdout.reconfigure(line_buffering=True)` para que la salida aparezca enseguida aunque se redirija a un archivo.
- `ej3_1`: los handlers se registran **antes** del `fork()`; si se registran después (como en el código original), hay una ventana mínima en la que una USR1 mataría al hijo (acción por defecto = terminar).
- `ej6`: el worker ignora SIGINT (si no, al apretar Ctrl+C cada worker ejecutaba el `_shutdown` heredado del supervisor y mataba a sus "hermanos") y el supervisor bloquea SIGCHLD durante el `fork()` + registro del PID, para no perder un hijo que muera antes de quedar anotado.
- `adicional_senales_comandos.py` hereda de `Servidor` (de `servidor_signals.py`), así que hay que correrlo desde esta carpeta.

## Qué se probó

Todo se corrió con `timeout` y las señales se mandaron con `kill` desde otro proceso:
- `comandos.sh`: STOP deja el `sleep` en estado `T`, CONT lo vuelve a `S`, TERM sale con 143; un proceso que ignora TERM sobrevive y se mata con `kill -9` (137). strace muestra `--- SIGUSR1 {si_code=SI_USER, si_pid=...} ---` y `+++ killed by SIGUSR1 +++`. (`man 7 signal` no está instalado en el contenedor de prueba; el script lo detecta.)
- 2.1: 3 x SIGINT → sale al tercero. 2.2: SIGTERM → libera los 3 recursos en orden inverso.
- 3.1: el contador del hijo llega a 3 y después a 5; el padre ve que el hijo murió por SIGTERM. 3.2: los 5 hijos se recogen con códigos 0..4, sin zombies.
- 4.1: la rápida devuelve "Completado", la lenta da Timeout a los 3 s. 4.2: stats cada 2 s (4, 8, 12, 16, 20).
- 5: USR1, HUP, USR2, USR1, TERM → todas las reacciones correctas y cleanup.
- 6: workers que terminan / fallan se reponen; con SIGINT al supervisor todos reciben SIGTERM y se recogen.
- Watchdog: `kill -9` al hijo → lo relanza; `kill` al watchdog → baja al hijo y sale. Rate limiter con N=4: exactamente 4 ops por segundo.
- Señales como comandos: 1, 2 y 3 USR1 separadas por 0.1 s funcionan. Mandando 3 `kill -USR1` pegados (sin pausa) **se contó 1 sola**: las señales estándar no se encolan (ver respuestas).

## Respuestas

**1.2 ¿Qué pasa con STOP / CONT / TERM / KILL?** STOP congela el proceso (en `ps` aparece `T`), no se puede capturar ni ignorar. CONT lo despierta y sigue donde estaba (el `sleep` sigue contando). `kill` sin opción manda SIGTERM: el proceso termina, pero podría capturarla o ignorarla; por eso SIGKILL (`-9`) es el último recurso: no se puede capturar, lo mata el kernel sin darle chance de limpiar nada. El código de salida en bash es 128 + número de señal (143 para TERM, 137 para KILL).

**1.3 ¿Qué muestra strace?** Primero un montón de `rt_sigaction` (Python consulta/instala handlers al arrancar) y después la llegada de la señal con quién la mandó (`si_pid`, `SI_USER` = vino de un `kill`). Como Python no tiene handler para USR1, se aplica la acción por defecto: `+++ killed by SIGUSR1 +++`.

**2.1 ¿Por qué no termina con el primer Ctrl+C?** Porque reemplazamos la acción de SIGINT por nuestro handler; la señal llega igual, pero en vez de levantar `KeyboardInterrupt` se ejecuta nuestra función, que solo cuenta. Recién al tercero levantamos `SystemExit`.

**2.2 ¿Por qué el handler solo cambia una bandera?** Porque el handler interrumpe al programa en cualquier punto; hacer el cleanup ahí adentro es riesgoso. Se marca `ejecutando = False` y el loop principal termina su vuelta y hace la limpieza en un lugar conocido.

**3.2 ¿Por qué el `while` con `WNOHANG` en el handler de SIGCHLD?** Si dos hijos terminan casi juntos, el kernel puede marcar un solo SIGCHLD pendiente (las señales estándar no se acumulan). Con un solo `waitpid` quedaría un zombie; el loop recoge todos los que ya terminaron y `WNOHANG` evita bloquearse si queda alguno vivo.

**4.1 / 4.2 ¿Qué observás?** La operación lenta se corta a los 3 s porque el handler de SIGALRM levanta una excepción en medio del `sleep`. El `finally` cancela la alarma (`alarm(0)`) para que no salte después en otra parte. En el timer periódico las stats aparecen cada 2 s mientras el loop sigue trabajando: el trabajo y el reporte están "intercalados" sin threads. Ojo: hay un solo SIGALRM por proceso, así que no se pueden combinar dos timers independientes con `alarm`/`ITIMER_REAL`.

**6 ¿Qué observás en el pool?** Cada worker que termina (bien o con error simulado) genera un SIGCHLD; el supervisor lo recoge y en la siguiente vuelta lanza uno nuevo para mantener 3. Al pedir shutdown se les manda SIGTERM a todos y el supervisor espera a que el handler de SIGCHLD los vaya sacando del diccionario.

**Señales como comandos - limitación:** si mandás varias USR1 muy pegadas, el kernel puede fusionarlas (mientras una USR1 está pendiente, otra igual se descarta). Por eso hay que espaciarlas un poco (0.1 s alcanza) o usar señales de tiempo real (SIGRTMIN+n), que sí se encolan.

**Rate limiter:** se usa un "balde" que SIGALRM recarga a N fichas por segundo. Se espera la ficha con un `sleep` cortito en vez de `signal.pause()` porque con `pause()` hay una carrera: si la alarma llega justo entre el chequeo y el `pause()`, el proceso se queda dormido hasta la siguiente alarma.
