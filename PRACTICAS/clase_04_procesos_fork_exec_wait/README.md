# Clase 4 — Procesos: fork, exec, wait

Todo se corre desde esta carpeta con Python 3.10+ (probado en Linux con Python 3.13). Solo usa la stdlib.

| Ejercicio | Archivo | Comando |
|---|---|---|
| 1. Primer fork | `ej1_primer_fork.py` | `python3 ej1_primer_fork.py` |
| 2. Crear N hijos | `ej2_n_hijos.py` | `python3 ej2_n_hijos.py` (opcional: `python3 ej2_n_hijos.py 8`) |
| 3. Patrón fork-exec | `ej3_fork_exec.py` | `python3 ej3_fork_exec.py` (por defecto `ls -la /tmp`) o `python3 ej3_fork_exec.py uname -a` |
| 4. Zombies | `ej4_zombie.py` | Sin wait: `python3 ej4_zombie.py` y en otra terminal `ps aux \| grep -E 'Z\|defunct'`. Con wait: `python3 ej4_zombie.py --wait` |
| 5. Mini-shell (obligatorio) | `ej5_minishell.py` | `python3 ej5_minishell.py` |
| 6. Código de salida como mensaje | `ej6_archivo_existe.py` | `python3 ej6_archivo_existe.py` (o pasarle rutas: `python3 ej6_archivo_existe.py /etc/hosts /nada`) |
| Adicional: watcher de archivos | `adicional_watcher.py` | `python3 adicional_watcher.py /tmp/prueba.txt 15` y en otra terminal `echo x >> /tmp/prueba.txt` |
| Adicional: pool manual | `adicional_pool_manual.py` | `python3 adicional_pool_manual.py 3` |

`ej_fork_exec.py` de la cátedra es solo un ejemplo, no se copió.

## Notas

- **Ej. 4:** el programa lee `/proc/<pid>/stat` y muestra el estado del hijo: con la versión sin `wait` aparece `Z` (zombie, `<defunct>` en `ps`); con `--wait` el hijo desaparece de `/proc`. El número opcional cambia los 30 s de espera (ej.: `python3 ej4_zombie.py 5`).
- **Ej. 5:** está basado en el shell de `contenido.md`. Le agregué `shlex.split` para respetar comillas, `export VAR=valor` y `&` para correr en background (los hijos de background se recogen con `waitpid(-1, WNOHANG)` antes de cada prompt, así no quedan zombies). Si el comando muere por una señal, el shell también lo avisa.

## Respuestas

- **Ej. 1 — ¿Por qué se ven dos salidas?** `fork()` devuelve dos veces: en el hijo devuelve 0 y en el padre devuelve el PID del hijo. El `getppid()` del hijo coincide con el PID del padre. El orden entre las líneas del padre y del hijo depende del scheduler, pero "Programa terminado" siempre sale al final porque el padre hace `wait`.
- **Ej. 1/2 — ¿Por qué `os._exit()` en el hijo?** Para que el hijo no siga ejecutando el código del padre (por ejemplo, el loop del fork) y para que no se vacíen dos veces los buffers de stdio heredados.
- **Ej. 2:** los hijos terminan en orden según cuánto duermen, pero el padre los recoge en el orden en que los creó, porque hace `waitpid(pid)` en ese orden. El código de salida llega con `WEXITSTATUS(status)`.
- **Ej. 3:** si `exec` funciona, nunca vuelve, porque la imagen del proceso se reemplaza. Por eso lo que viene después de `execvp` solo se ejecuta si falló, y ahí salimos con 127, igual que bash ("command not found").
- **Ej. 4 — ¿Qué se observa?** Sin `wait`, el hijo aparece como `Z` / `<defunct>` mientras el padre está vivo: ya no ocupa memoria, pero sí ocupa una entrada en la tabla de procesos, porque el kernel guarda su código de salida para el padre. Con `wait`, el padre recoge ese estado y el zombie desaparece. Si el padre muere sin hacer `wait`, init/systemd adopta al zombie y lo limpia.
- **Ej. 5 — ¿Por qué `cd` (y `exit`, `export`) tienen que ser internos?** Porque el directorio actual y el entorno son atributos de cada proceso. Si `cd` se ejecutara en un hijo, cambiaría el directorio del hijo, que muere enseguida, y el shell seguiría en el mismo lugar.
- **Ej. 6:** el código de salida sirve como un canal de comunicación de 8 bits (0–255). Alcanza para un sí/no, pero no para devolver datos de verdad; para eso están los pipes (clase 5).
- **Pool manual:** como el código de salida solo tiene 8 bits, el resultado se devuelve `% 256`. En el pool nunca hay más de N hijos vivos a la vez, porque se usa `os.wait()`, que devuelve el primero que termine, y en ese momento se lanza el siguiente.

## Qué se probó

Corrí todos los scripts con `timeout`:
- Ej. 1, 2, 3 y 6 con la salida esperada. En el ej. 3 también probé un comando inexistente (devuelve 127) y `false` (devuelve 1).
- Ej. 4: el zombie aparece como `Z` / `<defunct>` en `ps`; con `--wait` desaparece.
- Mini-shell con entrada por pipe: `echo` con comillas, `cd`, `pwd`, `false`, comando inexistente, `export` + `sh -c 'echo $FOO'`, `&` en background y `exit`.
- Watcher: detecta modificación y borrado, y el padre lo termina con SIGTERM.
- Pool con 3 workers y 10 tareas.
