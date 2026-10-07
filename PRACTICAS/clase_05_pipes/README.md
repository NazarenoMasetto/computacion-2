# Clase 5 — Pipes y redirección

Todo se corre desde esta carpeta con Python 3.10+ (probado en Linux con Python 3.13). Solo usa la stdlib.

| Ejercicio | Archivo(s) | Comando |
|---|---|---|
| 1.1 FDs en la terminal | `comandos.sh` (sección 1.1) | `bash comandos.sh` (o pegar los comandos de la consigna en una terminal interactiva) |
| 1.2 FDs en Python | `explorar_fds.py` | `python3 explorar_fds.py` |
| 2.1 Redirección con dup2 | `ej2_1_redireccion_dup2.py` | `python3 ej2_1_redireccion_dup2.py` y después `cat /tmp/salida.txt` (opcional: pasar otro archivo como argumento) |
| 2.2 stdout vs stderr | `separar_salidas.py` + `comandos.sh` (sección 2.2) | `bash comandos.sh` o, a mano: `python3 separar_salidas.py > solo_stdout.txt`, etc. |
| 3.1 Pipe padre-hijo | `ej3_1_pipe_padre_hijo.py` | `python3 ej3_1_pipe_padre_hijo.py` |
| 3.2 Pipe bidireccional | `ej3_2_pipe_bidireccional.py` | `python3 ej3_2_pipe_bidireccional.py` (opcional: `python3 ej3_2_pipe_bidireccional.py 7`) |
| 4.1 Pipeline de 2 comandos | `ej4_1_pipeline_dos.py` | `python3 ej4_1_pipeline_dos.py` |
| 4.2 Pipeline de 3 comandos | `ej4_2_pipeline_tres.py` | `python3 ej4_2_pipeline_tres.py` |
| 5. Mini-shell con redirección (obligatorio) | `ej5_minishell_redireccion.py` | `python3 ej5_minishell_redireccion.py` |
| 6.1 Filtro Unix | `mayusculas.py` | `echo "hola mundo" \| python3 mayusculas.py` |
| 6.2 Pipeline con subprocess | `ej6_2_pipeline_subprocess.py` | `python3 ej6_2_pipeline_subprocess.py` |
| 7. Named pipe (FIFO) | `escritor_fifo.py`, `lector_fifo.py` | Terminal 1: `python3 escritor_fifo.py` · Terminal 2: `python3 lector_fifo.py` |
| Adicional: tee casero | `mi_tee.py` | `ls -la \| python3 mi_tee.py salida.txt` (`-a` para agregar al final) |
| Adicional: monitor de pipe | `monitor.py` | `seq 1 100000 \| python3 monitor.py 20000 \| wc -l` |

`comandos.sh` corre todos los ejercicios de terminal (1.1, 2.2, 6.1, 7 y los adicionales) dentro de un directorio de `mktemp -d`, que se borra al final.

`fd_playground.py` y `pipe_playground.py` son material de la cátedra; no se copiaron.

## Notas de implementación

- **Mini-shell (ej. 5):** cumple todo el checklist. Soporta `>` (crea o trunca), `>>` (append, bonus), `<` (entrada, bonus), `cd` y `exit` internos, y usa `shlex` para las comillas (`echo "hola mundo" > test.txt`). Si el archivo de `<` no existe o el comando no existe, muestra el error y el código. Una línea como `ls >` (sin archivo) da error de sintaxis en vez de romper con `IndexError`, como pasaba con el esqueleto.
- **Ej. 4.1 y 4.2:** el código de la consigna hace `os.execvp(...)` seguido de `os._exit(1)`. Pero `execvp` no devuelve si falla: lanza `OSError`, así que el `_exit` nunca se ejecuta y el hijo sigue corriendo el código del padre. Lo corregí con `try/except` en `exec_o_morir()`.
- **FIFO:** los dos programas aceptan argumentos opcionales: el escritor `[cantidad] [intervalo] [ruta]` y el lector `[ruta]`. Cualquiera de los dos crea la FIFO si no existe, así que da igual cuál se lanza primero. Si el lector se va antes de tiempo, el escritor captura `BrokenPipeError`.
- **Filtros** (`mayusculas.py`, `mi_tee.py`, `monitor.py`): manejan `BrokenPipeError`, por ejemplo con `| head -1`. El monitor escribe las estadísticas en **stderr** para no mezclarlas con los datos que pasan por stdout.

## Respuestas

- **1.1 / 1.2 — ¿Qué se observa?** Todo proceso arranca con 0, 1 y 2 (stdin, stdout, stderr). Cuando se abre un archivo, el kernel le da **el fd libre más bajo** (3, después 4…). Al cerrar el 3, ese número queda libre y se reutiliza. En el script aparece también el 255: es el fd con el que bash lee el propio script. En Python puede aparecer un fd extra con error: es el que usó `os.listdir` para leer `/proc/<pid>/fd`, que ya se cerró cuando llega el `readlink`.
- **2.1 — ¿Por qué el `flush()`?** `print` escribe en un buffer de Python, no directo en el fd 1. Si no se vacía antes del `dup2`, el texto termina en el destino equivocado. Pasa, por ejemplo, cuando stdout no es una terminal y el buffer no se vacía por línea. La copia con `os.dup(1)` sirve para poder restaurar el stdout original.
- **2.2 — ¿Qué pasa con cada redirección?** `>` redirige solo el fd 1, así que los errores siguen saliendo por pantalla. `2>` redirige solo el fd 2. Con `> a 2> b` cada salida va a su archivo. `> todo.txt 2>&1` hace que el fd 2 apunte a lo mismo que el 1, y el orden importa: `2>&1 > todo.txt` dejaría stderr en la terminal. Los mensajes con `os.write` también se redirigen, porque la redirección pasa a nivel de fd, debajo de Python.
- **3.1 — ¿Por qué cerrar los extremos que no se usan?** `read` devuelve EOF (`b""`) recién cuando **todos** los extremos de escritura están cerrados. Si el padre no cierra su copia de `write_fd`, se queda bloqueado para siempre esperando datos. Además, un pipe es unidireccional y tiene un buffer en el kernel (64 KiB en Linux).
- **3.2:** para ir y volver hacen falta dos pipes. Si se usara uno solo, el padre podría leer su propio mensaje. El padre cierra `p2h_write` después de escribir para que el hijo sepa que no viene más nada.
- **4 — ¿Cómo arma el shell `ls | grep`?** Crea el pipe, hace un fork por cada comando, en cada hijo pone el extremo que corresponde en 0 o 1 con `dup2`, cierra todos los demás y hace `exec`. Los dos comandos corren **en paralelo**. Si el padre no cierra sus copias del pipe, el último comando nunca ve EOF y el pipeline se cuelga.
- **5:** la redirección se arma en el hijo, entre el `fork` y el `exec`. Como `exec` conserva los fds abiertos, el programa nuevo escribe en el archivo "sin saberlo". Por eso el shell no necesita que `ls` sepa nada de archivos.
- **6.1:** un filtro Unix lee de stdin y escribe en stdout, así que se puede encadenar con cualquier otro programa. Con `| head -5` el filtro puede recibir SIGPIPE/`BrokenPipeError` cuando `head` termina: es normal y hay que manejarlo.
- **6.2 — ¿Por qué cerrar `echo.stdout` y `grep.stdout` en el padre?** Para que el padre no se quede con copias de los extremos de lectura. Si `wc` o `grep` terminan antes, el proceso anterior recibe SIGPIPE en vez de quedarse bloqueado.
- **7 — ¿Qué pasa con la FIFO?** Es un pipe con nombre en el filesystem (`ls -l` muestra una `p`) y no guarda datos en disco. El `open` del escritor **se bloquea** hasta que hay un lector, y viceversa. Cuando el escritor cierra, el lector recibe EOF y su `for` termina. A diferencia de `os.pipe()`, la pueden usar procesos que no son parientes.
- **Tee / monitor:** son filtros "transparentes": copian stdin a stdout sin cambiarlo. `tee` además escribe en archivos, y el monitor manda las estadísticas por stderr para no mezclarlas con los datos.

## Qué se probó

Todo se corrió con `timeout`.
- `comandos.sh` completo: FDs del shell, las 4 redirecciones, el filtro, la FIFO con escritor en background, tee y monitor.
- Los scripts 1.2, 2.1, 3.1, 3.2, 4.1, 4.2 y 6.2 dan la salida esperada. En el 4.2 se comparó contra `grep -c root /etc/passwd`, y en el 4.1 también se probó un comando inexistente.
- Mini-shell con la secuencia de "Verificación" de la consigna, más `>>`, `<` combinado con `>`, `ls >` sin archivo, entrada inexistente, comando inexistente, `cd` y EOF (Ctrl+D).
- FIFO lanzando primero el lector, y con un lector que corta antes (`head -n1`).
- Filtros con `| head -1`: no muestran traceback.
