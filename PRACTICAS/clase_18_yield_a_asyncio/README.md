# Clase 18 — De yield a asyncio

Python 3.10+ (probado con 3.13 en Linux), solo stdlib. Casi todo son scripts que corren en una sola terminal.
El único que levanta un servidor es `ej5_bloqueo.py`: tiene su propio servidor HTTP interno, en el puerto 8080 por defecto, con `--port N` para cambiarlo.

## Archivos y cómo correrlos

| Ejercicio | Archivo(s) | Comando |
|---|---|---|
| 1 Generadores que reciben | `ej1_generadores.py` | `python3 ej1_generadores.py` |
| 2 Scheduler (obligatorio) | `ej2_scheduler.py` | `python3 ej2_scheduler.py` (todas) o `--parte a` / `b` / `c` / `d` |
| 3 Puente a async/await | `ej3_puente.py` (+ `puente.py` de la cátedra) | `python3 ej3_puente.py` |
| 4 asyncio de verdad | `ej4_asyncio.py` | `python3 ej4_asyncio.py` |
| 5 Cuándo sirve | `comparar.py` de la cátedra | `python3 ../../compu2_um_2026/clase_18_yield_a_asyncio/comparar.py` |
| 5.1 Encontrar el bloqueo | `ej5_bloqueo.py` | `python3 ej5_bloqueo.py [--port 8080]` (levanta un servidor HTTP lento local, sin internet) |
| Adicional: prioridades | `scheduler_prioridades.py` | `python3 scheduler_prioridades.py` |
| Adicional: egoístas | `detectar_egoistas.py` | `python3 detectar_egoistas.py [--umbral 0.1]` |
| Adicional: pipeline | `pipeline_generadores.py` | `python3 pipeline_generadores.py [archivo] [--patron texto]` |
| Adicional: leer el fuente | (respuesta abajo) | `grep -n "types.coroutine" /usr/lib/python3*/asyncio/*.py` |

## Qué se probó

Corrí todos los scripts con Python 3.13 en Linux (con `timeout`). Los números de abajo salen de esas corridas.
`ej5_bloqueo.py` usa el puerto 29200 en la prueba.

## Respuestas

### Ejercicio 1

1. `a.send(10)` sin `next()` da `TypeError: can't send non-None value to a just-started generator`. El generador no llegó a ningún `yield`, así que no hay dónde "aterrizar" el valor.
2. `next(a)` devuelve **0**: ejecuta hasta el primer `yield total`, con `total = 0`, y entrega ese valor.
3. `send(10)` → 10, `send(5)` → 15, `send(7)` → 22. Cada `send(n)` hace que el `yield` devuelva `n`, se ejecuta `total += n`, el bucle vuelve al `yield total` y se entrega el total acumulado.
4. No comparten `n`. Alternando: c1 imprime 0, 1, c2 imprime 0, c1 imprime 2, c2 imprime 1. Cada generador tiene su propio estado.
5. El `n` vive en el **frame** del generador (`gen.gi_frame.f_locals`), que queda guardado en el heap mientras está suspendido. En una función común el frame se destruye al hacer `return` y las locales desaparecen.
6. Imprime `resultado final`. El `return` de un generador no se "devuelve" porque llamar al generador no ejecuta nada: devuelve el objeto generador. El valor del `return` viaja dentro de la excepción `StopIteration` que termina la iteración, en `e.value`.
7. El scheduler atrapa `StopIteration` para saber que la tarea **terminó** y no reencolarla. Con `yield from`, Python usa `e.value` como valor de la expresión `yield from`.

### Ejercicio 2 (obligatorio)

**A.**
1. El orden es round-robin: `A1 B1 C1 A2 B2 C2 A3 [B termina] C3 [A termina] C4 [C termina]`. Se intercalan de a un paso y las cortas van saliendo.
2. Con A=3, B=2 y C=4 pasos, `next()` se llamó **12 veces**: 9 pasos más 3 llamadas finales que lanzan `StopIteration` (una por tarea).
3. Una "tarea" sin `yield` es una **función común**: al llamarla se ejecuta entera de una y devuelve `None`. El scheduler después falla con `TypeError: 'NoneType' object is not an iterator`. Se ejecutó, pero fuera de su control.

**B.**
4. Durante los 3 s del `time.sleep(3)`, **A y C quedan congeladas**: A dio su paso 1 a los 0,01 s y el paso 2 recién a los 3,01 s. Nadie puede sacarle el control a la egoísta.
5. Con threads no habría pasado: el SO (y el GIL cada ~5 ms) **interrumpe** a un hilo para darle CPU a otro. Eso es concurrencia **preventiva** (preemptive): el planificador quita el control. En la **cooperativa** cada tarea decide cuándo cederlo, y si no lo cede nadie puede quitárselo.
6. La regla es **"no bloquear el event loop"**: toda tarea tiene que ceder seguido y nunca hacer llamadas bloqueantes. Es la misma conclusión del ejercicio 7 de la clase 17: un callback pesado congela a todos los clientes del servidor con selectors.

**C.**
7. `dormir(segundos)` hace `yield time.monotonic() + segundos`: le dice al scheduler cuándo quiere volver. El scheduler la reencola con esa hora y no la reanuda antes. Mi scheduler, además, cuando no hay ninguna tarea lista duerme hasta el próximo despertar en vez de girar en vacío (como el `timeout` de `select()`).
8. Porque `time.sleep()` bloquea **el hilo entero**, que es el único, y con él al scheduler y a todas las tareas. Sería una tarea egoísta. `dormir()` tiene que ceder el control y dejar que el scheduler haga otras cosas mientras tanto.
9. Tres tareas de 0,15 s, cinco corridas: **0,150 s cada vez**, contra 0,45 s si fuera la suma. Con A:3, B:2 y C:4 esperas tardó 0,60 s (4 × 0,15, la tarea más larga), contra 1,35 s de suma. Las esperas **se solapan**: mientras una espera, las otras corren o esperan en paralelo. El total es el de la tarea más larga.

**D.**
10. `yield from dormir(espera)` **delega** en el subgenerador: cada `yield` de `dormir` sube directo hasta el scheduler, y los `send()` bajan hasta `dormir`. Llamar `dormir(espera)` a secas solo **crea** el objeto generador, y su código no corre nunca.
11. Sin el `yield from`, las tareas no esperan nada: tardó **0,000 s** y además dejaron de intercalarse (A hizo sus 3 pasos seguidos y después B). No falla ruidosamente porque crear un generador y tirarlo es perfectamente legal en Python. A diferencia de las corrutinas `async`, que avisan con `RuntimeWarning: coroutine ... was never awaited`, un generador descartado no avisa nada.

### Ejercicio 3

1. `async def` devuelve un objeto **`coroutine`**, y **no se ejecutó nada** del cuerpo: igual que un generador recién creado.
2. `hasattr(c, 'send')` → `True`, y `c.send(None)` lanza `StopIteration` con `value = 99`.
3. Es el mismo mecanismo del 1.3: el `return` de la corrutina viaja en `StopIteration.value`. El event loop hace exactamente eso: `send(None)` para arrancar, y cuando recibe `StopIteration` toma `.value` como resultado de la tarea.
4. Que `await` y `yield from` son **la misma maquinaria**. `await` acepta un generador marcado con `@types.coroutine`, su `yield` sube a través de la corrutina hasta quien hizo `send()`, y el `send('hola')` baja hasta el generador. `async/await` es una sintaxis distinta sobre el mismo protocolo de generadores.
5. Traducción (en `ej3_puente.py`, que además la ejecuta). `@asyncio.coroutine` ya no existe: se eliminó en Python 3.11.
   ```python
   async def buscar(id):
       conn = await abrir()
       datos = await leer(conn, id)
       return datos
   ```
6. Resolvió dos problemas:
   - **Ambigüedad**: con `yield from` no se distinguía un generador de datos de una corrutina. Era fácil pasar uno donde iba el otro, o que un `yield` "suelto" convirtiera una función en generador sin querer. `async def` marca explícitamente que es una corrutina, con un tipo propio, y no se puede iterar por accidente.
   - **Errores silenciosos y legibilidad**: olvidarse el `yield from` no avisaba nada (lo vimos en 2.11). Con `await`, una corrutina no awaiteada da `RuntimeWarning`, y `await` fuera de `async def` es `SyntaxError`. También habilitó `async for` / `async with`, y el código se lee como "esperar a" en vez de "delegar en un generador".

### Ejercicio 4

1. La `deque` la reemplaza la **cola de listos del event loop** (`loop._ready`, las Tasks programadas) y el `while pendientes` lo reemplaza `loop.run_forever()` / `run_until_complete()` dentro de `asyncio.run()`. El `yield` se vuelve `await asyncio.sleep(0)`. La salida es idéntica a la del scheduler a mano (A1 B1 C1 A2…).
2. Sin `await`, `asyncio.gather()` devuelve un `_GatheringFuture`, `main` termina enseguida y `asyncio.run()` **cancela** las tareas pendientes. Llegaron a dar un solo paso cada una y aparece `_GatheringFuture exception was never retrieved ... CancelledError`.
3. Dos `asyncio.run()` seguidos **funcionan sin problema**: cada uno crea un loop nuevo y lo cierra al terminar (eso es lo que puede sorprender: no hay un "loop global" que se rompa). Lo que no se puede es llamarlo **adentro** de una corrutina que ya corre: `RuntimeError: asyncio.run() cannot be called from a running event loop`. Además queda el aviso de que la corrutina que le pasamos nunca se awaiteó.
4. `saludar()` solo **crea** la corrutina y no imprime nada. Cuando se destruye, Python avisa `RuntimeWarning: coroutine 'saludar' was never awaited`. Con `asyncio.run(saludar())` sí imprime `hola`, porque alguien la ejecuta (le hace `send`).
5. Es lo mismo que con los generadores: crearlo no ejecuta nada hasta el primer `next()`. La diferencia es que el generador abandonado no avisa y la corrutina sí.
6. Terminan en orden de duración: **b (0,1), c (0,2), a (0,3)**.
7. `gather` devuelve los resultados **en el orden de los argumentos**: `['a', 'b', 'c']`, sin importar cuál terminó primero.
8. `gather(a(), b(), c())` las corre **concurrentes**: **1,00 s**. El `for ... await f()` las corre **una tras otra**: **3,00 s**. `await` espera a que termine antes de seguir. Para solaparlas hay que programarlas juntas (gather / create_task).

### Ejercicio 5

1. Números de mi máquina:

   | Caso | Tiempo |
   |---|---|
   | I/O secuencial | 3,00 s |
   | asyncio + `asyncio.sleep` | 1,00 s |
   | asyncio + `time.sleep` | 3,00 s |
   | CPU secuencial | 5,40 s |
   | CPU con asyncio | 5,60 s |

   En I/O-bound asyncio mejora **3×** (lo que tarda la tarea más larga y no la suma).
2. Con `time.sleep()` adentro tarda **3,00 s**, igual que secuencial. `time.sleep()` no cede el control: bloquea el único hilo, así que el loop no puede pasar a la siguiente corrutina hasta que termina.
3. En CPU-bound asyncio **da igual o empeora un poco** (5,40 → 5,60 s). Hay un solo hilo haciendo trabajo real y no hay esperas que solapar.
4. Porque asyncio agrega trabajo sin sacar nada a cambio: crear Tasks y Futures, el `gather`, las vueltas del loop, los callbacks. Ese overhead es chico pero se suma al mismo cálculo.
5. Regla: **asyncio conviene cuando el programa pasa la mayor parte del tiempo esperando I/O (red, disco, timers) con muchas operaciones concurrentes, y siempre que todo lo que se use adentro sea no bloqueante.**
6. Sí, es el mismo criterio que con threads y el GIL: **I/O-bound → threads o asyncio** (las esperas se solapan); **CPU-bound → procesos** (multiprocessing / ProcessPoolExecutor). La diferencia es que asyncio es cooperativo y en un hilo (escala a miles de tareas baratas pero no tolera bloqueos), mientras que los threads son preventivos.

**5.1 Encontrar el bloqueo** (`ej5_bloqueo.py`, 5 descargas de un servidor local que tarda 1 s):

| Forma | Tiempo |
|---|---|
| `urllib` adentro de la corrutina | **5,06 s** |
| `urllib` con `asyncio.to_thread` | 1,01 s |
| `asyncio.open_connection` (HTTP a mano) | 1,00 s |

7. `urllib.request.urlopen(...).read()` es **bloqueante**: hace `connect`/`recv` con sockets bloqueantes y nunca hace `await`. Cada corrutina se queda con el hilo hasta terminar la descarga y las cinco van en fila.
8. Una biblioteca HTTP asíncrona: `aiohttp` o `httpx.AsyncClient` (fuera de la stdlib), o `asyncio.open_connection()` a mano. Como parche, envolver lo bloqueante en `await asyncio.to_thread(...)` / `loop.run_in_executor(...)`.
9. Llamadas bloqueantes comunes que no van en una corrutina: `time.sleep()` (usar `asyncio.sleep`), `requests.get()` / `urllib.request.urlopen()`, `socket.recv()`/`accept()` bloqueantes, `open().read()` de archivos grandes, `input()`, drivers de base de datos síncronos (`sqlite3`, `psycopg2`), `subprocess.run()`, y cálculos largos de CPU.

### Adicionales

- **Scheduler con prioridades**: en vez de la `deque` conviene un **heap** (`heapq`), ordenado por un "tiempo virtual" que avanza `1/peso` en cada turno. Con pesos 3:2:1, en 30 turnos salió `ALTA: 15, media: 10, baja: 5`: proporción exacta y sin que la baja se muera de hambre.
- **Detectar tareas egoístas**: el scheduler mide cada `next()` y avisa: `"EGO" tuvo el control 0.400s sin ceder (umbral 0.1s)`. Con asyncio real y `loop.set_debug(True)` aparece el log `Executing <Task ... egoista_async() ...> took 0.300 seconds`. Lo mismo, con el umbral `slow_callback_duration = 0.1`.
- **Pipeline de generadores**: `leer_lineas → filtrar → contar`, cada etapa empuja con `send()` a la siguiente y el cierre se propaga con `close()` / `GeneratorExit`. Un decorador `@arrancar` hace el `next()` inicial (el "priming" del 1.1). Sobre el propio script con patrón `yield`, contó 4 líneas.
- **Leer el fuente**: en Python 3.13, `asyncio/tasks.py` usa `@types.coroutine` en `__sleep0()`, un generador con un `yield` pelado que usa `asyncio.sleep(0)` para ceder una vuelta del loop. Hace falta el puente porque **una corrutina `async def` no puede hacer `yield`** para suspenderse ante el loop: solo puede hacer `await` de otro awaitable. En el fondo de toda cadena de `await` tiene que haber algo que haga un `yield` de verdad hacia `Task.__step`. Ese algo es `__sleep0` (decorado con `types.coroutine`) o el `__await__` de `Future`, que es un generador con `yield self` (`futures.py`). Es el mismo rol que tenía `dormir()` en nuestro scheduler.
