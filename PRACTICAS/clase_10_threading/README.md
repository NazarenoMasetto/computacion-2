# Clase 10: Threading

Solo stdlib, Python 3.10+. No hace falta `pip install` (el descargador y el crawler usan `urllib`).

| Ejercicio | Archivo(s) | Comando |
|---|---|---|
| 1. Primer hilo | `ej1_primer_hilo.py` | `python3 ej1_primer_hilo.py` |
| 2. Tiempos I/O-bound | `ej2_io_bound.py` | `python3 ej2_io_bound.py` |
| 3. GIL (CPU-bound) | `ej3_gil_cpu_bound.py` | `python3 ej3_gil_cpu_bound.py [N]` |
| 4. Clase Thread | `ej4_clase_thread.py` | `python3 ej4_clase_thread.py` |
| 5. Race condition y Lock | `ej5_race_lock.py` | `python3 ej5_race_lock.py` |
| 6.1 Sin daemon | `ej6a_sin_daemon.py` | `python3 ej6a_sin_daemon.py` (cortar con Ctrl+C) |
| 6.2 Con daemon | `ej6b_con_daemon.py` | `python3 ej6b_con_daemon.py` |
| 7. Productor-consumidor | `ej7_productor_consumidor.py` | `python3 ej7_productor_consumidor.py` |
| 8. `threading.local()` | `ej8_threading_local.py` | `python3 ej8_threading_local.py` |
| 9. Descargador paralelo (obligatorio) | `ej9_descargador.py` | `python3 ej9_descargador.py` (URLs de la consigna) o `python3 ej9_descargador.py -w 3 URL1 URL2 ...` |
| Adicional: chat multi-hilo | `ej10_chat_multihilo.py` | `python3 ej10_chat_multihilo.py` |
| Adicional: monitor de sistema | `ej11_monitor_sistema.py` | `python3 ej11_monitor_sistema.py` (10 s, cada 2 s) o `python3 ej11_monitor_sistema.py 4 1` |
| Adicional: crawler básico | `ej12_crawler.py` | `python3 ej12_crawler.py https://pypi.org -w 4 -m 10` |

## Qué se probó

Todo se corrió en Linux, Python 3.13, máquina de 2 cores (tiempos dependientes de la máquina):

- ej2: secuencial 5.00 s, threading 1.00 s → **5.0x**.
- ej3 (4 tareas, N=2.000.000, GIL activo): secuencial 0.91 s, 2 threads 0.93 s, 4 threads 0.92 s, 4 procesos 0.44 s (2.05x, el máximo con 2 cores).
- ej5: sin lock el saldo terminó en **-1000**; con lock en 0 (5 retiros OK y 5 rechazados).
- ej6a: corrido con `timeout -s INT 5` (simula Ctrl+C): siguió imprimiendo después de que "terminó" el main hasta recibir la señal. ej6b terminó solo a los 3 s.
- ej7: 20 imágenes en 2.50 s (secuencial serían 10 s), 5 por worker.
- ej9 y ej12: probados contra un `python3 -m http.server 26000` local (páginas OK, 404, puerto cerrado 26999 → connection refused, URL mal formada) y contra internet. Por el proxy del entorno de prueba, de las URLs de la consigna solo bajó `pypi.org`; las otras dieron `Tunnel connection failed: 403`, que el programa reporta como error sin crashear (que es justamente lo que pide la consigna). En una red normal deberían bajar las 5.
- ej10, ej11 (con `4 1`), ej1, ej4, ej8: OK.

## Respuestas

**Ej 1** — Las líneas de los 3 hilos salen intercaladas y a veces "pegadas" en la misma línea (`[Hilo-2] número: 1[Hilo-3] número: 1`): `print` escribe el texto y el `\n` por separado y otro hilo se mete en el medio. El orden entre hilos no está garantizado; "Listo" siempre sale último por los `join()`.

**Ej 2** — Threading da ~5x porque `time.sleep` (igual que esperar la red o el disco) **libera el GIL**: los 5 hilos esperan a la vez, el tiempo total es el de la descarga más lenta (~1 s) y no la suma.

**Ej 3** — Con GIL, los threads no mejoran nada en CPU-bound (0.98x–0.99x): sólo un hilo ejecuta bytecode Python a la vez, así que se turnan y encima pagan los cambios de contexto. Con `multiprocessing.Process` cada proceso tiene su propio intérprete y su propio GIL, y ahí sí se usan los 2 cores (2.05x). (En un Python 3.13 "free-threaded" sin GIL los threads sí escalarían; el script muestra si el GIL está activo.)

**Ej 4** — Al heredar de `Thread` se sobreescribe `run()` (no `start()`); `start()` crea el hilo y él llama a `run()`. Guardar el resultado en un atributo es una forma simple de "devolver" algo desde un hilo, que se lee después del `join()`.

**Ej 5** — La race condition está en el patrón *check-then-act*: los 10 hilos pasan el `if saldo >= monto` mientras el saldo todavía es 1000 (el `sleep` agranda la ventana) y después todos restan → -1000. La solución es que el chequeo **y** la resta estén dentro del mismo `with lock:`; poner el lock sólo en la resta no alcanza.

**Ej 6** — Un hilo no-daemon mantiene vivo el proceso: aunque el main llegue al final, Python espera (`threading._shutdown`) a todos los no-daemon, y como el loop es infinito no termina nunca (hay que matarlo con Ctrl+C). Un hilo daemon se mata de golpe cuando termina el último hilo no-daemon, así que el programa termina a los 3 s. Ojo: al morir de golpe no se ejecuta ningún `finally`/limpieza, por eso los daemons no sirven para cosas que tienen que cerrar archivos o conexiones prolijamente.

**Ej 7** — 20 imágenes × 0.5 s = 10 s secuencial; con 4 workers ≈ 20/4 × 0.5 = 2.5 s (medido 2.50 s). La `Queue` ya es thread-safe, no hace falta lock para la cola; sí para el dict `resultados` compartido. `cola.join()` espera a que cada `get` tenga su `task_done()`, y después se mandan los `None` (uno por worker) para que salgan del loop.

**Ej 8** — `threading.local()` da un objeto donde cada hilo ve sus propios atributos: aunque todos escriben `contexto.usuario`, ninguno pisa al otro (el script lo verifica con un `assert` después del `sleep`), y el hilo principal ve todo en `None`. Sirve para no tener que pasar el contexto (usuario, conexión a la BD, request) como parámetro por todas las funciones.

**Ej 9** — Cumple: pool fijo de `-w` workers (no un thread por URL) alimentados por una `queue.Queue`, descargas en paralelo, errores de red capturados (`URLError`/`HTTPError`, `OSError` para timeouts y conexión rechazada, `ValueError` para URL mal formada) sin crashear, y estadísticas finales (exitosas, errores, bytes, tiempo total vs suma de tiempos individuales, qué worker bajó cada una). La lista de resultados se protege con `Lock`.

**Crawler** — Es un solo nivel: baja la URL inicial, saca los `<a href>` con `html.parser`, los pasa a absolutos con `urljoin`, descarta fragmentos `#`, `mailto:` y repetidos, y los descarga con un pool limitado (`-w`) y un máximo de enlaces (`-m`).

## Salteado

Nada; `extra_manijas.md` no se hizo (por consigna).
