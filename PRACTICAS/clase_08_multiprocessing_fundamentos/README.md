# Clase 8 — Multiprocessing: fundamentos

Todo se corre desde esta carpeta con Python 3.10+ (probado en Linux con Python 3.13). Solo usa la stdlib. Todos los scripts tienen el guard `if __name__ == "__main__":`, así que también funcionan con `spawn`.

| Ejercicio | Archivo | Comando |
|---|---|---|
| 1. Tu primer Process | `ej1_primer_process.py` | `python3 ej1_primer_process.py` |
| 2. 5 workers en paralelo | `ej2_cinco_workers.py` | `python3 ej2_cinco_workers.py` |
| 3. Productor-consumidor con Queue | `ej3_productor_consumidor.py` | `python3 ej3_productor_consumidor.py` |
| 4. Pipe bidireccional (ping-pong) | `ej4_pipe_ping_pong.py` | `python3 ej4_pipe_ping_pong.py` |
| 5. fork vs spawn | `ej5_fork_vs_spawn.py` | `python3 ej5_fork_vs_spawn.py` (compara los dos). Uno solo: `python3 ej5_fork_vs_spawn.py spawn [N]` (también acepta `forkserver`) |

En el ej. 5, `set_start_method()` se puede llamar una sola vez por programa. Por eso, sin argumentos, el script se relanza a sí mismo una vez con `fork` y otra con `spawn`: es literalmente "el mismo programa" corrido con cada método. Mide el tiempo de los 100 `start()` y el de `start()` + `join()`.

## Respuestas

- **Ej. 1 — ¿Qué pasos te ahorrás con `Process` respecto de `os.fork()`?** No hay que distinguir ramas con `if pid == 0`: el código del hijo es una función (`target`) y los datos se pasan con `args`. Tampoco hay que acordarse de `os._exit()` para que el hijo no siga ejecutando el código del padre, ni decodificar el status con `WIFEXITED`/`WEXITSTATUS`: está `p.exitcode`, que además es negativo si lo mató una señal. `join()` reemplaza a `waitpid`. Y el mismo código anda en Windows/macOS (con spawn), cosa que `os.fork()` no.
- **Ej. 2:** el tiempo total queda cerca de la **duración máxima** y no de la suma: en una corrida dio 1.85 s de total, con un máximo de 1.83 s y una suma de 6.34 s. Los procesos duermen en paralelo, y la diferencia es el costo de crearlos y hacer `join`.
- **Ej. 3:** para avisar el fin uso una "píldora venenosa" (`None`): cuando el consumidor la saca de la cola, termina. Productor y consumidor se intercalan y la `Queue` se encarga del pickle y la sincronización. El consumidor devuelve cuántos ítems procesó por una segunda cola.
- **Ej. 4:** `multiprocessing.Pipe()` es duplex por defecto: cada extremo puede hacer `send` y `recv` de objetos Python (con pickle por debajo). A diferencia de `os.pipe()`, no hacen falta dos pipes ni manejar bytes. Como cada `recv` bloquea hasta que llega la respuesta, el ping-pong sale siempre alternado.
- **Ej. 5 — Resultados (esta máquina, 100 procesos, start+join):**

  | Método | Tiempo total | Por proceso |
  |---|---|---|
  | fork | ~0.20 s | ~2 ms |
  | forkserver | ~0.37 s | ~3.7 ms |
  | spawn | ~5.4 s | ~54 ms |

  `spawn` es más de 20 veces más lento: cada hijo arranca un intérprete nuevo, re-importa el módulo y recibe la función por pickle. `fork` solo duplica el proceso con copy-on-write. `forkserver` queda en el medio: hace fork desde un servidor "limpio", pero paga la comunicación con ese servidor. A cambio, `spawn` es portable y da un estado limpio, sin locks ni threads heredados. Nota: en Linux, el default es `fork` hasta Python 3.13; desde 3.14 pasó a ser `forkserver`.

## Qué se probó

- Todos los scripts corrieron con `timeout` en Linux con Python 3.13 y dieron la salida esperada.
- Los ej. 1 a 4 también se corrieron forzando `spawn` (`set_start_method('spawn')` antes de llamar a `main()`) y funcionan igual.
- El ej. 5 se corrió con fork, spawn y forkserver. Los tiempos dependen de la máquina.
