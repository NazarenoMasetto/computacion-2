# TP2 — Plataforma de Tareas Distribuidas

**Computación II — Universidad de Mendoza — 2026**
Alumno: Nazareno Masetto

API HTTP para mandar trabajos a ejecutar en segundo plano. Cada trabajo
entra a una cola, un grupo de workers asíncronos los va tomando y el cliente
puede preguntar en cualquier momento cómo va cada uno y qué devolvió. Toda la
plataforma vive en un único proceso con un único event loop de asyncio; lo
único que sale de ese hilo es el cálculo pesado, que va a un executor de
threads.

---

## 1. Descripción y uso

### Cómo arrancarlo

```bash
docker compose up --build
```

Cuando el log dice `Uvicorn running`, la API responde en el puerto 8000 del
host. FastAPI genera además una página para probar los endpoints desde el
navegador en `http://localhost:8000/docs`.

Configuración (variables de entorno en `docker-compose.yml`):

| Variable | Default | Qué controla |
|----------|---------|--------------|
| `WORKERS` | 4 | Cantidad de workers del pool (se puede cambiar al levantar: `WORKERS=50 docker compose up --build`) |
| `TIMEOUT_DEFAULT` | 30 | Timeout (s) de una tarea si no se indica otro |
| `ESPERA_APAGADO` | 10 | Cuánto se espera a las tareas en curso al apagar |
| `DIR_ESTADO` | `/app/datos` | Dónde se escriben los volcados (montado en `./datos`) |

### Endpoints

| Método | Ruta | Qué hace |
|--------|------|----------|
| `POST` | `/tareas` | Encola una tarea. Responde `202` con su `id` y estado `pendiente` |
| `GET` | `/tareas?estado=...` | Lista las tareas, con filtro opcional por estado |
| `GET` | `/tareas/{id}` | Estado y resultado de una tarea |
| `DELETE` | `/tareas/{id}` | Cancela una tarea pendiente o en ejecución (`409` si ya terminó) |
| `GET` | `/estadisticas` | Totales por estado, tiempo promedio, workers ocupados y vivos, tamaño de la cola |

Una tarea arranca `pendiente`, pasa a `ejecutando` cuando la toma un worker y
termina en uno de tres estados finales: `completada`, `fallida` o `cancelada`.

### Tipos de tarea

| Tarea | Qué recibe | Tipo de carga |
|-------|-----------|---------------|
| `descargar` | `urls: list[str]`, `concurrente: bool = true` | I/O-bound |
| `hashear` | `texto: str`, `iteraciones: int = 1000000`, `bloqueante: bool = false` | CPU-bound |
| `esperar` | `segundos: float = 1` | I/O simulado |

`concurrente=false` y `bloqueante=true` existen **solo para las mediciones**:
permiten comparar la versión correcta contra la incorrecta usando el mismo
sistema.

Cualquier tarea acepta además `timeout` (segundos).

### Ejemplos con curl

```bash
# Encolar una descarga concurrente
curl -X POST localhost:8000/tareas -H 'content-type: application/json' \
  -d '{"tipo":"descargar","parametros":{"urls":["https://example.com","https://www.python.org"]}}'

# 5 millones de SHA-256: se calcula en un thread aparte, la API no se traba
curl -X POST localhost:8000/tareas -H 'content-type: application/json' \
  -d '{"tipo":"hashear","parametros":{"texto":"hola","iteraciones":5000000}}'

# Tarea con timeout: duerme 10 s pero el límite es 2 s -> queda "fallida"
curl -X POST localhost:8000/tareas -H 'content-type: application/json' \
  -d '{"tipo":"esperar","parametros":{"segundos":10},"timeout":2}'

# Consultar, listar, filtrar, cancelar
curl localhost:8000/tareas/<id>
curl localhost:8000/tareas
curl "localhost:8000/tareas?estado=ejecutando"
curl -X DELETE localhost:8000/tareas/<id>

# Estadísticas
curl localhost:8000/estadisticas
```

### Apagado ordenado

`Ctrl+C` (SIGINT) o `docker compose stop` (SIGTERM) disparan el apagado:
a partir de ese momento un `POST` recibe `503`; las tareas que ya estaban
corriendo tienen `ESPERA_APAGADO` segundos para terminar y, si no llegan, se
cancelan; recién entonces se frenan los workers y se escribe
`datos/estado_<timestamp>.json` con todo el estado. Al arrancar, si hay
volcados previos, se informa por log.

### Mediciones

Con el sistema levantado, en otra terminal:

```bash
python3 mediciones.py                     # las tres
python3 mediciones.py --solo 2            # una sola
python3 mediciones.py --repeticiones 5    # más repeticiones
```

Las mediciones 1 y 2 se repiten 3 veces por defecto y se informa la mediana.
Los datos crudos de cada corrida quedan en `resultados/` como JSON. Solo usa
la biblioteca estándar de Python.

---

## 2. Arquitectura

```
  Cliente HTTP (curl, navegador, mediciones.py)
        │
        ▼
┌─────────────────────────────────────────────────────────┐
│  UN PROCESO · UN HILO · UN EVENT LOOP (uvicorn)         │
│                                                         │
│  FastAPI                                                │
│   POST /tareas ──► crea Tarea(pendiente), la guarda en  │
│                    el dict `tareas` y hace              │
│                    cola.put_nowait(id) ──► responde 202 │
│   GET / DELETE ──► leen o modifican `tareas`            │
│                         │                               │
│                         ▼                               │
│                ┌─────────────────┐                      │
│                │  asyncio.Queue  │  (ids de tareas)     │
│                └────────┬────────┘                      │
│                         │ await cola.get()              │
│        ┌─────────┬──────┴──┬─────────┐                  │
│        ▼         ▼         ▼         ▼                  │
│    worker-0  worker-1  worker-2  worker-3  (corrutinas) │
│        │                                                │
│        │ job = create_task(...)                         │
│        │ await wait_for(job, timeout)                   │
│        ▼                                                │
│   esperar ──► asyncio.sleep                             │
│   descargar ► httpx.AsyncClient + gather                │
│   hashear ──► asyncio.to_thread ──────────┐             │
│                                           │             │
└───────────────────────────────────────────┼─────────────┘
                                            ▼
                               ThreadPoolExecutor
                               (threads del sistema)
```

### Flujo de una tarea

1. Pydantic revisa el JSON del `POST`. Si está bien, se arma la `Tarea`
   (todavía `pendiente`), se agrega al diccionario `tareas` y su `id` va a la
   cola con `put_nowait`. La respuesta `202` sale en ese mismo momento.
2. Del otro lado, algún worker estaba parado en `await cola.get()` sin
   consumir nada. Apenas aparece el `id`, el event loop lo reactiva.
3. El worker la pasa a `ejecutando` y crea una `Task` aparte (`job`) que corre
   la función del tipo correspondiente. Espera ese `job` con
   `asyncio.wait_for(job, timeout)`.
4. Según cómo termine: `completada` con su resultado, `fallida` con el motivo
   (excepción o timeout) o `cancelada` (DELETE o apagado).
5. El worker hace `task_done()` y vuelve a `cola.get()`.

### Archivos

| Archivo | Contenido |
|---------|-----------|
| `app/main.py` | API FastAPI, `lifespan` (arranque/apagado), configuración |
| `app/pool.py` | Cola, workers, cancelación, timeouts, apagado y volcado |
| `app/tareas.py` | Implementación de `descargar`, `hashear` y `esperar` |
| `app/modelos.py` | Estados, tipos de tarea y modelos Pydantic |
| `mediciones.py` | Script de las tres mediciones |

---

## 3. Decisiones de diseño

### ¿Por qué `asyncio.Queue` y no `queue.Queue`?

`queue.Queue.get()` es **bloqueante**: frena el hilo que la llama hasta que
haya un elemento. Como todo el sistema corre en un único hilo (el del event
loop), un worker esperando en una `queue.Queue` vacía congelaría la API
entera. Con `asyncio.Queue` es distinto porque `get()` es una corrutina: un
worker sin trabajo queda "estacionado" en ese `await`, y mientras tanto el
event loop atiende requests y a los demás workers. El `put` del endpoint es lo
que lo vuelve a poner en marcha.

Además, `queue.Queue` usa locks internos pensados para varios threads, que acá
no hacen falta: `asyncio.Queue` no es thread-safe, pero tampoco lo necesita,
porque solo la usa el hilo del event loop.

### ¿Cómo evito que una tarea CPU-bound congele la API?

El event loop es cooperativo: solo puede cambiar de corrutina cuando la que
está corriendo hace `await`. Un loop de 5 millones de `sha256` no tiene ningún
`await` adentro, así que mientras corre el loop no puede atender nada (eso es
exactamente lo que muestra la medición 2).

La solución es sacar ese cómputo del hilo del event loop con
`asyncio.to_thread(...)`, que lo manda a un thread del `ThreadPoolExecutor` por
defecto y devuelve un *awaitable*. El worker hace `await` sobre eso: se
suspende, el loop queda libre, y cuando el thread termina el loop retoma al
worker con el resultado.

**Limitación honesta:** esto evita congelar la API, pero no da paralelismo
real. `hashlib.sha256` solo libera el GIL para entradas de más de 2047 bytes, y
acá se hashean 32 bytes por vez, así que dos hashes en dos threads se turnan el
GIL y tardan lo mismo que uno detrás del otro (se ve en la medición 3b). Para
paralelismo real habría que usar `ProcessPoolExecutor` (ver *Limitaciones*).

### ¿Cómo implementé la cancelación y qué pasa con los recursos a medio usar?

La clave es que el worker no ejecuta la tarea directamente: la lanza como una
`asyncio.Task` aparte (el `job`) y se queda esperándola. Como son dos `Task`
distintas, un `DELETE` puede cancelar el `job` y el worker sobrevive.

- **Tarea pendiente:** no se puede sacar un elemento del medio de una
  `asyncio.Queue`, así que solo se cambia su estado a `cancelada`. El `id`
  sigue en la cola, y el worker que lo reciba revisa el estado y pasa de largo.
- **Tarea en ejecución:** además de marcarla, se llama `job.cancel()`. Ese
  llamado hace que el próximo (o el actual) `await` del job lance
  `CancelledError`, y la excepción va subiendo por la corrutina como cualquier
  otra.

Qué pasa con los recursos en cada tipo:

- **`esperar`:** el `CancelledError` sale de `asyncio.sleep` y listo, no hay
  nada que liberar.
- **`descargar`:** el cliente HTTP está dentro de `async with
  httpx.AsyncClient()`. El `CancelledError` atraviesa el bloque y `__aexit__`
  cierra las conexiones abiertas. `gather` además cancela las descargas
  hermanas que seguían en curso. Si se cancela a mitad de una descarga, esa
  respuesta parcial se descarta y el socket se cierra.
- **`hashear`:** un thread no se puede matar desde afuera. Cancelar el `await`
  de `to_thread` libera al worker, pero el thread seguiría quemando CPU. Por
  eso la cancelación es **cooperativa**: se le pasa un `threading.Event`, al
  cancelar se hace `set()`, y el thread lo revisa cada 10.000 iteraciones y
  corta solo.

El worker distingue *quién* fue cancelado con
`asyncio.current_task().cancelling()`: si es 0, se canceló solo el job (un
DELETE) y el worker sigue con la cola; si es mayor que 0, están cancelando al
worker mismo (apagado) y la excepción se propaga. Esta verificación surgió de
un bug real que apareció durante las pruebas: si el apagado coincidía con una
tarea ya marcada como cancelada, el worker se "tragaba" su propia cancelación
y el apagado quedaba colgado para siempre.

Los **timeouts** usan `asyncio.wait_for(job, timeout)`, que al vencer cancela
el job (mismo mecanismo de arriba) y lanza `TimeoutError`; el worker lo
convierte en estado `fallida` con el motivo.

### ¿Qué pasa si un worker lanza una excepción no capturada?

Un error dentro de una tarea **no tumba al worker que la corría**: `_procesar`
captura `Exception`, registra el traceback en el log y deja la tarea en
`fallida` con `"TipoDeError: mensaje"`. Por ejemplo, un parámetro mal escrito
(`{"seg": 1}`) termina en `fallida` con un `TypeError` y el worker sigue
atendiendo.

Además, `cola.task_done()` está en un `finally`, así que la cuenta de la cola
queda bien aunque algo falle. Si a pesar de eso un worker muriera (un bug en
el propio código del pool), asyncio no lo reinicia solo: el pool quedaría con
un worker menos. Para que eso no pase inadvertido, `/estadisticas` informa
`workers_vivos` además de `workers` (la cantidad configurada). Es una de las
limitaciones conocidas.

Un caso borde relacionado: si llega un `DELETE` justo en el instante en que la
tarea termina, el `DELETE` ya la marcó `cancelada`. Por eso el worker solo
escribe el resultado si la tarea sigue en `ejecutando`; así el estado final
coincide con lo que la API le respondió al cliente.

---

## 4. Mediciones

Entorno: notebook ASUS TUF Gaming F15 (FX506LHB), Ubuntu, Docker ·
4 workers · internet hogareña.

Los números de esta sección salieron de una corrida de `python3 mediciones.py`
(una repetición por medición) contra el
sistema levantado con `docker compose up --build`.

### 4.1 Concurrencia I/O: 20 descargas

| Modo | Tiempo total |
|------|-------------|
| Secuencial (`for` + `await`) | 11,836 s |
| Concurrente (`asyncio.gather`) | 2,229 s |
| **Speedup** | **5,3x** |

Las 20 descargas respondieron bien (20/20 en ambos modos). En el modo
secuencial, la suma de los tiempos individuales fue 11,827 s, prácticamente
igual al total. En el concurrente, la descarga más lenta tardó 2,196 s y el
total fue 2,229 s.

**Interpretación.** En el modo secuencial, cada descarga empieza recién
cuando terminó la anterior, así que el total es la suma de todas. Con
`gather`, las 20 peticiones salen casi a la vez: mientras una espera la
respuesta del servidor, el event loop avanza las otras. El total se acerca a
lo que tarda la más lenta, no a la suma: 2,229 s de total contra 2,196 s de
la más lenta, una diferencia de apenas 33 ms, que es lo que cuesta crear el
cliente HTTP y lanzar y juntar las 20 corrutinas.

El speedup no llega a 20x porque las descargas no duran todas lo mismo:
la más lenta (2,2 s) fija el piso del modo concurrente, mientras que en
promedio cada una tarda unos 0,6 s. Como el modo concurrente nunca puede
tardar menos que su descarga más lenta, el speedup máximo posible era
`tiempo secuencial / más lenta` = 11,84 / 2,20 ≈ 5,4x, y medimos 5,3x: la
concurrencia aprovechó prácticamente todo lo que se podía aprovechar. Para mejorar más
habría que acelerar el sitio más lento, cosa que no depende de nosotros.

### 4.2 Event loop bloqueado

Hash de 5.000.000 iteraciones, midiendo `GET /tareas` mientras corre:

| Caso | Latencia promedio | Latencia máxima |
|------|-------------------|-----------------|
| En reposo | 1,3 ms | — |
| Sin executor (`bloqueante=true`) | 2653,8 ms | 2653,8 ms |
| Con executor (`to_thread`) | 20,9 ms | 31,7 ms |

Sin executor el hash tardó 2,85 s y en todo ese lapso **se pudo hacer un
solo `GET`**. Con executor el hash tardó 3,25 s y se hicieron 23 `GET`.

**Interpretación.** Sin executor, el `GET` no tarda poco ni mucho: tarda
**lo que le falte al hash para terminar**. El script manda el `GET` unos
200 ms después de lanzar el hash, y el `GET` tardó 2,65 s: justo lo que le
faltaba a un hash de 2,85 s. El request llega al socket, pero el event loop
está ocupado dentro del `for` de `sha256` y no vuelve a llamar a
`epoll` hasta que termina; recién ahí ve la conexión y la atiende. Durante
todo ese tiempo la API está muerta para todos los clientes, no solo para
quien pidió el hash.

Con executor, el hash corre en otro thread y el loop sigue atendiendo: los
`GET` responden en unos 21 ms, **127 veces más rápido** que sin executor. La
latencia sube respecto del reposo (de 1,3 a 21 ms) porque el thread del hash
compite por el GIL con el hilo del loop: Python le saca el GIL al thread cada
5 ms aproximadamente (`sys.getswitchinterval()`) para que el loop pueda
avanzar, y eso hace que cada `GET` tenga que esperar algunos turnos. Por la
misma razón el hash tarda un poco más con executor (3,25 s contra 2,85 s):
comparte el GIL con el loop. Es un precio chico a cambio de que el servidor
nunca deje de responder.

### 4.3 Techo del pool

**a) Tareas I/O (`esperar` de 1 s):**

| N tareas | Total (s) | Tareas/s |
|----------|-----------|----------|
| 1 | 1,06 | 0,95 |
| 2 | 1,05 | 1,91 |
| 4 | 1,01 | 3,96 |
| 8 | 2,01 | 3,98 |
| 16 | 4,07 | 3,93 |
| 32 | 8,09 | 3,96 |
| 64 | 16,03 | 3,99 |

**b) Tareas CPU (`hashear` de 1.000.000 iteraciones, con executor):**

| N tareas | Total (s) | s/tarea |
|----------|-----------|---------|
| 1 | 0,63 | 0,63 |
| 2 | 1,28 | 0,64 |
| 4 | 2,49 | 0,62 |
| 8 | 4,99 | 0,62 |

**Interpretación.**

Hay **dos techos distintos**:

1. **Para I/O, el techo es la cantidad de workers.** Hasta 4 tareas, todas
   terminan en ~1 s porque corren a la vez. A partir de 5, las que sobran
   esperan en la cola a que se libere un worker: 8 tardan 2,01 s, 16 tardan
   4,07 s, 64 tardan 16,03 s, y el rendimiento se estanca en ~3,96 tareas/s,
   que es `WORKERS / duración` = 4 / 1 s. El tiempo total sigue exactamente
   `⌈N / 4⌉` segundos: las tareas se procesan en "tandas" de 4. No es un
   límite de asyncio (el loop podría tener miles de `sleep` en vuelo) sino del
   diseño: el pool limita cuántas tareas se ejecutan a la vez. Subir `WORKERS`
   sube el techo casi linealmente para tareas I/O.

2. **Para CPU, no hay paralelismo: el techo es 1 núcleo.** El tiempo por
   tarea se mantiene constante (~0,62 s) sin importar cuántas corran a la
   vez: 8 hashes tardan 4,99 s, que es 8 × 0,62. Con 4 tareas hay 4 workers
   y 4 threads del executor trabajando al mismo tiempo, y aun así tardan lo
   mismo que 4 hashes uno detrás del otro, aunque la notebook tiene varios
   núcleos libres. Es el **GIL** (clase 10): los threads del executor se
   turnan para ejecutar bytecode de Python, y `sha256` sobre 32 bytes no
   libera el GIL. El executor sirve
   para no congelar la API, no para ir más rápido. Agregar workers acá no
   mejora nada.

---

## 5. Conceptos del curso aplicados

- **Productor-consumidor (clase 11).** `POST /tareas` es el productor y los
  workers son los consumidores de una `asyncio.Queue` compartida. Es el mismo
  patrón que hicimos con threads, pero con corrutinas.

- **Por qué no hace falta `Lock` (clase 11 vs. clases 18-21).** Con threads,
  el scheduler del sistema operativo puede sacarle la CPU a un hilo en el
  peor momento posible, y por eso `tareas[id].estado = ...` necesitaría un
  lock. Con
  asyncio, una corrutina solo cede el control en un `await`. En `cancelar()`,
  `_procesar()` o `encolar()`, entre leer el estado de una tarea y
  escribirlo no hay ningún `await`, así que ningún otro worker o request
  puede meterse en el medio. Todo el estado compartido (`tareas`, `en_curso`,
  la cola) se toca solo desde el hilo del event loop.

- **Sockets y servidores concurrentes (clases 13-14).** Uvicorn es, en el
  fondo, un servidor TCP que acepta conexiones. La diferencia con el servidor
  de un thread por cliente que vimos es que acá todas las conexiones las
  atiende un solo hilo.

- **I/O multiplexing con `select`/`epoll` (clase 17).** Es lo que hace que lo
  anterior funcione: el event loop registra todos los sockets (los de los
  clientes HTTP y los de las descargas de `httpx`) en `epoll` y duerme hasta
  que alguno tenga datos. Por eso 20 descargas en vuelo no necesitan 20
  threads. Y por eso la medición 2 muestra lo que muestra: si el loop está
  calculando hashes, no llega a llamar a `epoll`, y nadie atiende los
  sockets.

- **De `yield` a `async/await` (clase 18).** Una corrutina es un generador
  con otra sintaxis: `await` suspende la función guardando su estado, igual
  que `yield`, y el event loop la retoma con `send()` cuando lo que esperaba
  está listo. La cancelación es el equivalente a `throw()`: el loop inyecta
  un `CancelledError` en el punto donde la corrutina está suspendida. Por eso
  los `async with` y `finally` de las tareas se ejecutan al cancelar.

- **HTTP y FastAPI (clase 19).** `POST` devuelve `202 Accepted` (recibido, no
  procesado), `404` para ids inexistentes, `409 Conflict` para cancelar algo
  ya terminado y `503` durante el apagado. Pydantic valida los cuerpos antes
  de que lleguen al pool.

- **Asyncio en red (clase 20).** `descargar` usa `httpx.AsyncClient` y
  `gather`. La diferencia entre `gather` y un `for` con `await` adentro es
  exactamente la medición 1: el `for` espera cada corrutina antes de crear la
  siguiente; `gather` las lanza todas y espera a que terminen juntas.

- **Asyncio avanzado: colas, cancelación, timeouts, executors (clase 21).**
  `asyncio.Queue`, `Task.cancel()`, `wait_for`, `to_thread` y
  `Task.cancelling()` son el núcleo de `pool.py`.

- **`concurrent.futures` (clase 22).** `to_thread` usa por debajo el
  `ThreadPoolExecutor` por defecto del loop. La medición 3b muestra por qué
  para CPU-bound haría falta un `ProcessPoolExecutor`.

- **Señales (clase 6).** Uvicorn instala handlers para `SIGINT` y
  `SIGTERM`; el apagado ordenado corre en el `lifespan` cuando llega una de
  ellas. En el `Dockerfile`, el `CMD` está escrito como lista (forma *exec*)
  y no como texto: así no hay un `sh` en el medio que se quede con la señal, y
  el `SIGTERM` de `docker stop` le llega a uvicorn.

### Respuestas a las preguntas de la corrección

- **¿Dónde podría bloquear el event loop?** En `hashear` con
  `bloqueante=true` (a propósito, para la medición 2) y en `volcar()`, que
  escribe el JSON de forma síncrona. Esto último es aceptable porque ocurre
  una sola vez, durante el apagado, cuando ya no se atienden requests. Con
  muchísimas tareas, `GET /tareas` y `/estadisticas` recorren todo el
  diccionario y también bloquean proporcionalmente a su tamaño.
- **¿Qué pasa si cancelo a mitad de una descarga?** Ver sección 3: el
  `CancelledError` sale del `await cliente.get()`, `gather` cancela las
  hermanas y el `async with` cierra las conexiones.
- **¿Por qué el pool no necesita `Lock`?** Ver arriba: un solo hilo y no hay
  `await` entre leer y escribir el estado.
- **¿Qué se rompe primero con 10.000 tareas de golpe?** La cola es
  ilimitada, así que los 10.000 `POST` se aceptan y se encolan bien. Lo que
  se degrada primero es `GET /tareas`: devuelve las 10.000 tareas en un solo
  JSON y su serialización bloquea el loop cada vez que alguien lo pide. Las
  tareas en sí avanzan de a `WORKERS` por vez, así que las últimas esperan
  mucho en la cola. No vencen por timeout, porque el timeout se cuenta desde
  que la tarea empieza a ejecutarse y no desde que se encola: simplemente
  tardan. Y la memoria crece sin límite porque nunca se borran las tareas
  terminadas.
- **¿`gather` vs. `for` con `await`?** Ver sección 4.1.
- **¿Por qué `time.sleep()` es un bug y `asyncio.sleep()` no?**
  `time.sleep()` duerme **el hilo**, y en asyncio hay un solo hilo: se
  congela todo el servidor. `asyncio.sleep()` es una corrutina que le dice al
  loop "despertame en N segundos" y le devuelve el control para que atienda
  otras cosas mientras tanto.

---

## 6. Limitaciones conocidas

- **CPU-bound sin paralelismo real.** Por el GIL, varios `hashear` a la vez
  no aprovechan varios núcleos. Se resolvería con `ProcessPoolExecutor`, a
  costo de serializar argumentos y de que la cancelación cooperativa con
  `threading.Event` no sirva entre procesos (habría que usar
  `multiprocessing.Event` o un `Manager`).
- **Cola sin límite y memoria sin límite.** No hay `maxsize` en la cola ni
  limpieza de tareas terminadas: con suficiente carga, la memoria crece
  indefinidamente. Lo correcto sería devolver `429`/`503` cuando la cola está
  llena y purgar tareas viejas.
- **`GET /tareas` sin paginación.** Con muchas tareas, la respuesta es
  enorme y serializarla bloquea el loop.
- **El volcado no se restaura.** Al arrancar se informa que existe, pero las
  tareas pendientes no se vuelven a encolar.
- **Un solo proceso.** Si el proceso muere de golpe (SIGKILL, OOM), se pierde
  todo el estado desde el último volcado. No es "distribuido" en el sentido
  de varias máquinas.
- **Cancelación de `hashear` con latencia.** El thread revisa el `Event` cada
  10.000 iteraciones, así que puede seguir corriendo unos milisegundos
  después del `DELETE`.
- **Si un worker muere por un bug del propio pool, no se reinicia.**
- **`descargar` no limita la concurrencia por tarea.** Una tarea con 1.000
  URLs abre hasta 100 conexiones a la vez (el límite por defecto de `httpx`).

### ¿Por qué `httpx` y no `aiohttp`?

Las dos son asíncronas y sirven. Se eligió `httpx` porque tiene una API casi
igual a `requests` (la biblioteca HTTP más conocida de Python), funciona tanto
en modo síncrono como asíncrono, tiene timeouts por defecto y es lo que usa FastAPI en sus propios
tests. `requests` quedaba descartado por ser bloqueante: cada descarga
congelaría el loop igual que `time.sleep()`.

---

## 7. Lo que aprendí

Lo que más me sorprendió fue ver el event loop bloqueado con mis propios
números. Yo sabía que una tarea pesada "bloquea", pero no me imaginaba que
fuera tanto: sin executor, un simple `GET` tardó 2,6 segundos, y con executor
tardó 21 ms. Ahí me cayó la ficha de que en asyncio nadie frena a una
corrutina; si no hace `await`, el resto del programa se queda esperando.

También pensaba que mandar el hash a un thread lo iba a hacer más rápido, y no
fue así: por el GIL, varios hashes juntos tardaron lo mismo que uno atrás del
otro. O sea, el executor sirve para que la API no se cuelgue, no para ganar
velocidad. Lo que más me costó fue la cancelación, porque hay que distinguir
cuándo se cancela una tarea y cuándo se está apagando todo el servidor. A
diferencia del TP1, acá no necesité locks porque todo corre en un solo hilo.
