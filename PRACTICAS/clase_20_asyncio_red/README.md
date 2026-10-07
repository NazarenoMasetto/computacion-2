# Clase 20: Asyncio en red

## Instalación

```bash
python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt
```

Solo `ej3_descargas_http.py` y `servidor_prueba.py` necesitan dependencias. Todo lo demás usa la biblioteca estándar.

## Ejercicios → archivos → comandos

Todos los servidores usan el puerto de la consigna y aceptan otro por argumento (o `--puerto` en `eco_async.py`) o por la variable `PUERTO`.

| Ejercicio | Archivo(s) | Comandos |
|---|---|---|
| 1. Servidor eco | `eco_async.py` (le agregué `--puerto`, `--bloqueante` para el punto 1.6 y `--sin-drain` para el 2.2) | `python3 eco_async.py` + varios `nc localhost 8080` · `python3 eco_async.py --lento 3` · `python3 eco_async.py --lento 3 --bloqueante` · `kill -TERM $(pgrep -f eco_async)` |
| 1.2 comparar threads | `server_threads.py` de la clase 14 | `python3 <repo-cátedra>/clase_14_servidores_concurrentes/server_threads.py` + 3 `nc` · `ls /proc/$(pgrep -f server_threads)/task \| wc -l` |
| 2.1 write/drain | `ej2_drain.py` (cliente que manda 100 MB sin leer; mide el RSS del servidor) | `python3 ej2_drain.py` (corre los dos casos) · o a mano: `python3 ej2_drain.py servidor 8080 [--sin-drain]` y `python3 ej2_drain.py cliente 8080` |
| 2.2 formas de leer | `ej2_lecturas.py` | `python3 ej2_lecturas.py` |
| 3. Concurrencia de clientes (**obligatorio**) | `descargas.py` (parte A), `ej3_descargas_http.py` (partes B, C, D), `servidor_prueba.py` (reemplazo local de example.com) | `python3 descargas.py` · `python3 servidor_prueba.py &` · `python3 ej3_descargas_http.py` · `python3 ej3_descargas_http.py --muchas 200 --ulimit 150` · con internet: `--url https://example.com` |
| 4. Locks | `ej4_locks.py` | `python3 ej4_locks.py` |
| 5. Timeouts y cancelación | `ej5_timeouts.py`, `descargas.py` (cancelación) | `python3 ej5_timeouts.py` |
| 6. La escala | `escala.py` (le agregué `PUERTO`) | `python3 escala.py` · `python3 escala.py 2000 5000` · `python3 escala.py 10000 15000` |
| Adicional: chat | `chat_async.py` | `python3 chat_async.py` + varios `nc localhost 8080` |
| Adicional: comandos | `comandos_async.py` | `python3 comandos_async.py` + `nc localhost 8080` (AYUDA, TIME, ECHO x, QUIEN, CONTADOR, QUIT) |
| Adicional: proxy | `proxy_async.py` | `python3 eco_async.py &` · `python3 proxy_async.py localhost 8080 9090` · `nc localhost 9090` |
| Adicional: esqueleto del TP2 | — | **Salteado**: es parte de la entrega del TP2. |

### Verificación del ejercicio obligatorio (ejercicio 3)

```bash
python3 descargas.py
python3 servidor_prueba.py &                       # o --url https://example.com si hay red
python3 ej3_descargas_http.py
python3 ej3_descargas_http.py --muchas 200 --ulimit 150
```

Mis números (10 descargas, el servidor de prueba tarda 0.5 s por pedido):

| Medición | Tiempo |
|---|---|
| `descargas.py` secuencial / gather / semáforo(4) / timeout 0.8 s | 5.72 s / 0.85 s / 1.56 s / 0.80 s (1 cancelada) |
| HTTP secuencial, un `AsyncClient` compartido | 5.19 s |
| HTTP secuencial, un `AsyncClient` por descarga | 5.92 s |
| HTTP `gather`, `AsyncClient` compartido | 0.61 s |
| HTTP `gather` con `requests` adentro | 5.05 s |
| HTTP `gather` con `Semaphore(3)` | 2.13 s |
| 200 sin semáforo con `ulimit -n 150` (y sin el límite de pool de httpx) | 144 ok / 56 `ConnectError` ← `OSError: [Errno 24] Too many open files` |
| 200 con `Semaphore(50)`, mismo ulimit | 200 ok |

- [x] Medición de secuencial contra `gather`, con números propios.
- [x] Por qué `gather` tarda lo que la más lenta: punto 3.1.
- [x] Descargas reales con `httpx` y un `AsyncClient` reutilizado.
- [x] Probé `requests` adentro de una corrutina: tarda lo mismo que la versión secuencial.
- [x] Semáforo implementado y medido.
- [x] Dos problemas que evita acotar la concurrencia: punto 3.8.
- [x] Probé `return_exceptions=True` y elegí cuál conviene para el TP2: puntos 3.11 y 3.12.

## Qué se probó

- **Sin salida a internet:** el proxy del entorno bloquea `example.com` (403 `host_not_allowed`). Las descargas "reales" las hice contra `servidor_prueba.py`, un FastAPI local que responde una página de 1 KB con 0.5 s de latencia. Son descargas HTTP de verdad (httpx, keep-alive, etc.), pero la latencia es simulada. Con red se corre igual con `--url https://example.com`.
- Todo se corrió con Python 3.13, en 2 cores, con `ulimit -n` = 20000.
- Ejercicio 1: 3 clientes `nc` contra `eco_async.py` (1 thread) y contra `server_threads.py` (4 threads en `/proc/<pid>/task`); `--lento 3` con dos clientes simultáneos, con y sin `--bloqueante`; SIGTERM con clientes conectados.
- Ejercicio 2: `ej2_drain.py` (los dos casos), `ej2_lecturas.py`, y `eco_async.py --sin-drain` con `nc`.
- Ejercicios 3 a 6: todo corrido, con los números de abajo.
- Adicionales: chat con 2 clientes `nc`; comandos con todos los comandos y 2 conexiones; proxy contra `eco_async.py` con `nc`, con 2 MB verificados byte a byte y con el destino caído.
- Lo que no probé: el comportamiento contra `example.com` de verdad, por la falta de red.

## Respuestas

### Ejercicio 1

1. Con tres clientes, el servidor reporta `threads: 1` en cada conexión, y `/proc/<pid>/task` también da 1.
2. `server_threads.py` de la clase 14 con 3 clientes: `ls /proc/<pid>/task | wc -l` → **4** (el principal más uno por cliente).
3. En el servidor con threads, cada conexión es un **thread** del sistema operativo, con su stack. En asyncio, cada conexión es un **objeto**: una `Task` que envuelve una corrutina más su par `StreamReader`/`StreamWriter`, y vive en el mismo hilo que todas las demás.
4. No. Con `--lento 3`, los dos clientes recibieron su eco a los **3.01 s**, al mismo tiempo.
5. Porque `await asyncio.sleep(3)` suspende solo esa corrutina: le devuelve el control al loop y agenda un temporizador. Mientras tanto, el loop sigue atendiendo a los otros clientes.
6. Con `time.sleep` (`--bloqueante`), el cliente 1 recibe a los 3.00 s y el cliente 2 a los **6.00 s**. `time.sleep` bloquea el único hilo, que es el que corre el event loop, y nadie más es atendido hasta que termina. Las esperas se serializan.
7. Imprime `Cerrando: no se aceptan conexiones nuevas`. Con Python 3.12 o más nuevo, `async with srv` (`wait_closed()`) **espera a que los clientes conectados se vayan**: el proceso siguió vivo hasta que los `nc` cerraron, y recién ahí imprimió `- (...) (conectados: 1)`, `- (...) (conectados: 0)` y terminó. Es un cierre ordenado: no acepta nuevos y deja terminar a los que están. En versiones anteriores, `asyncio.run` cancelaba las tareas pendientes y se veía `cancelada`.
8. `signal.signal()` instala un handler que Python ejecuta **en cualquier punto** del hilo principal, entre dos bytecodes, interrumpiendo lo que se estaba haciendo. `loop.add_signal_handler()` registra un callback que el **event loop** corre como un callback más, entre tareas. Por dentro usa el truco del self-pipe (`signal.set_wakeup_fd`).
9. Porque dentro de un handler de señal solo es seguro hacer muy pocas cosas (async-signal-safety). Si la señal cae en medio de una operación sobre el estado del loop, del buffer o de un lock, y el handler toca ese mismo estado, puede romperlo o trabarse. Con `add_signal_handler`, el callback (`cerrar.set`) corre en un momento seguro, cuando ninguna tarea está a mitad de camino, así que puede tocar cualquier estructura de asyncio sin riesgo.

### Ejercicio 2

1. `write()` no bloquea nunca: copia los bytes al buffer del transporte y vuelve enseguida, así que no hay nada que esperar. `drain()` **puede tener que esperar**: si el buffer pasó el límite alto (64 KB), se suspende hasta que el kernel lo vacíe por debajo del límite bajo. Por eso es una corrutina.
2. Sí, con `nc` funciona igual (`--sin-drain` → `ECO: anda igual`). Con mensajes chicos y un cliente que lee, el buffer nunca se llena.
3. Sirve para el **control de flujo (backpressure)**. Con `ej2_drain.py` y un cliente que manda 100 MB sin leer nunca:
   - **Con drain:** el servidor leyó 4.2 MB, su buffer de salida nunca pasó de 0.1 MB y el RSS se mantuvo en ~21 MB. El cliente quedó **frenado por TCP** a los 8.8 MB. drain suspendió al handler, el handler dejó de leer, se llenaron los buffers del kernel y TCP frenó al emisor.
   - **Sin drain:** el servidor leyó los 100 MB, el buffer de salida llegó a **96 MB** y el RSS pasó de 20 a **117 MB**. Con más datos o más clientes así, se queda sin memoria.
4. Con `'hola\nmundo\n'`: `read(100)` → `b'hola\nmundo\n'` (lo que haya, hasta 100); `readline()` → `b'hola\n'`; `readexactly(4)` → `b'hola'`; `readuntil(b'\n')` → `b'hola\n'`. El resto queda en el buffer para la próxima lectura.
5. `readline()` y `readuntil()` son framing por **delimitador**. `readexactly(n)` es framing por **longitud** (lo que se usa con un header de largo o con `Content-Length`). `read(n)` no hace framing: es como `recv`.
6. `readexactly(100)` con 11 bytes y el cliente cerrado lanza `asyncio.IncompleteReadError: 11 bytes read on a total of 100 expected bytes`. La excepción trae los bytes parciales en `.partial`.
7. `read()` devuelve `b''` cuando el otro lado cerró. Es el mismo `recv() == b''` de la clase 13, la señal de EOF.

### Ejercicio 3 (obligatorio)

1. Los cuatro tiempos de `descargas.py`: **5.72 s** secuencial, **0.85 s** gather, **1.56 s** con semáforo de 4, **0.80 s** con timeout de 0.8 s. Con `gather` todas las esperas se solapan: arrancan casi juntas y el loop solo espera timers, así que el total es la más lenta (0.9 s), no la suma (5.7 s).
2. Con `Semaphore(4)` corren como mucho 4 a la vez: son "tandas", y cada lugar que se libera lo toma la siguiente. El total queda entre la más lenta (todas a la vez) y la suma (de a una), aproximadamente suma/4 (≈1.4 s) más el desbalanceo de las tandas.
3. Con el timeout de 0.8 s se canceló **1** (la de 0.9 s). `asyncio.timeout` le inyectó `CancelledError` en su `await asyncio.sleep`: la corrutina se interrumpió y no siguió corriendo en segundo plano. Afuera se vio como `TimeoutError` y se devolvió `'tX TIMEOUT'`.
4. Con 10 descargas: 5.19 s secuencial contra 0.61 s concurrente, **unas 8.5 veces más rápido**. Con latencia de red real, la mejora es parecida: casi todo el tiempo de una descarga es esperar.
5. Porque el `AsyncClient` tiene un **pool de conexiones keep-alive** (clase 19). Si lo compartís, las descargas al mismo host reutilizan las conexiones TCP (y TLS) ya abiertas, en vez de pagar el handshake cada vez. Medido en secuencial: 5.19 s compartido contra 5.92 s con un cliente por descarga, y eso que es en localhost y sin TLS. Con https a un host remoto la diferencia es mucho mayor. Además, crear y cerrar clientes sin control deja sockets a medio cerrar.
6. Con `requests` adentro de la corrutina, el `gather` tarda **5.05 s**, lo mismo que la versión secuencial. `requests.get` es bloqueante: no tiene `await`, así que mientras espera la red el event loop está congelado y las corrutinas se ejecutan una detrás de la otra. Es el `/async-mal` de la clase 19.
7. Con `Semaphore(3)`: **2.13 s**, que son 4 tandas (3+3+3+1) × 0.5 s.
8. Acotar evita: (a) **agotar los descriptores de archivo** (`ulimit -n`): cada conexión es un fd; (b) **saturar al servidor remoto** o que te bloquee o te limite la tasa (429) por abrir cientos de conexiones (hasta parece un ataque); (c) saturar tu propia red, el ancho de banda y la memoria (cada respuesta en vuelo ocupa buffers).
9. Con 200 URLs sin semáforo y `ulimit -n 150`: 144 bien y 56 con `httpx.ConnectError: All connection attempts failed`, cuya causa es `OSError: [Errno 24] Too many open files`. Ojo: el `AsyncClient` por defecto ya trae un límite de 100 conexiones (un semáforo escondido). Para ver el error hay que sacarlo (`Limits(max_connections=None)`). Con `Semaphore(50)` las 200 anduvieron bien.
10. Con `gather` normal, la primera excepción (`ConnectError: Name or service not known`) **se propaga** y perdés la lista de resultados entera. Las otras tareas **no se cancelan**: siguieron corriendo y las 4 terminaron bien en segundo plano, pero sus resultados se pierden.
11. Con `return_exceptions=True`, `gather` no lanza nada: devuelve la lista completa, y en el lugar de la URL inválida pone el objeto excepción. Las 4 buenas dieron `200 1026 bytes`.
12. Para el TP2 quiero **`return_exceptions=True`** (o un try/except dentro de cada tarea). Cada tarea es independiente: que una URL falle no tiene que tirar abajo ni ocultar el resultado de las otras. Necesito marcar cada una como completada o fallida con su error. Con `gather` normal, un solo fallo hace perder todo y deja tareas sueltas corriendo.

### Ejercicio 4

1. Sí, 1000 corrutinas dan **1000**.
2. Con 1000 threads × `contador += 1` también me dio 1000, y 8 threads × 100 000 dio 800 000 (Python 3.13: el GIL solo cambia de thread en ciertos puntos, como los saltos de bucle y las llamadas, y en este caso no cae en el medio). Pero no está garantizado. Cuando metí un `time.sleep(0)` entre leer y escribir (que suelta el GIL), 1000 threads dieron **584**. Con threads el cambio de contexto lo decide el sistema operativo o el intérprete, en cualquier momento.
3. Porque las corrutinas son cooperativas y corren en un solo hilo: el cambio de tarea **solo** ocurre en un `await`. `contador += 1` no tiene ningún `await`, así que ninguna otra corrutina puede meterse en el medio. La sección es atómica por construcción.
4. No. Con 100 transferencias de 10 desde A=1000 quedó `A=990, B=1000`: el total pasó a 1990, o sea que se creó plata. Debería ser A=0.
5. Porque hay un `await` **dentro** de la sección crítica: todas las corrutinas leen `saldo = 1000`, se suspenden en el `sleep(0)`, y después cada una escribe `1000 - 10`. Es el mismo lost update de los threads, pero el punto de cambio es explícito (el `await`) en vez de arbitrario.
6. Con `asyncio.Lock` dio `A=0, B=1000`. Se usa `async with` porque adquirir el lock **puede tener que esperar** a que otro lo suelte, y esa espera tiene que ser un `await` que le devuelva el control al loop. Un `with` sincrónico bloquearía el hilo, o directamente no está soportado: `asyncio.Lock` no tiene `__enter__`.
7. La regla: **en asyncio hace falta un lock solo cuando una sección crítica (leer, decidir y escribir estado compartido) tiene un `await` en el medio.** Si no hay `await` adentro, es atómica.

### Ejercicio 5

1. Lanza `TimeoutError`, el builtin. Desde Python 3.11, `asyncio.TimeoutError` es el mismo objeto: `type(e) is asyncio.TimeoutError` → `True`.
2. **Se cancela.** `operacion_lenta()` recibió `CancelledError` en su `await` a los 2 s, corrió su `finally` y no siguió corriendo. El timeout convierte esa cancelación en `TimeoutError` hacia afuera.
3. `asyncio.wait_for(coro, 2)` hace lo mismo: cancela la operación y lanza `TimeoutError` (también lo medí, a los 2.00 s). Las diferencias son de forma: `timeout()` es un context manager que puede abarcar varios `await` y se puede reprogramar (`reschedule`); `wait_for` envuelve un solo awaitable. En 3.12 o más nuevo, `wait_for` está implementado con `timeout()`.
4. El orden de los mensajes de `descargas.py`: (1) `la tarea recibió CancelledError en su await`, (2) `finally: limpieza hecha`, (3) `quien la canceló también la ve`.
5. `cancel()` no interrumpe nada en el momento: marca la tarea. El `CancelledError` se **inyecta en el `await` en el que la tarea está suspendida** (el `asyncio.sleep(10)`) la próxima vez que el loop la despierta. Si la tarea está corriendo, lo recibe en su próximo `await`.
6. No funciona. Con un cálculo de 5 s sin `await`, el `cancel()` que debía llegar a los 0.5 s recién se ejecutó a los **5.50 s**: el loop estuvo bloqueado y ni el cancelador ni el timer pudieron correr. La tarea devolvió su resultado normal (`cancelled() = False`). Con `asyncio.timeout(0.5)` alrededor pasó lo mismo: devolvió el resultado a los 5.00 s **sin** `TimeoutError`. La cancelación es cooperativa: sin un `await`, no hay punto donde inyectarla. Para cálculo pesado hay que usar `run_in_executor` con procesos.
7. Si la atrapás y no la relanzás, la tarea **sigue corriendo como si nada**: quien canceló recibió `'terminé igual'` y `tarea.cancelled() = False`. Dentro de un `asyncio.timeout(0.1)`, el "timeout de 0.1 s" duró **0.70 s** y no lanzó `TimeoutError`. El síntoma es que las cancelaciones, los timeouts y los apagados (por ejemplo, `asyncio.run` o un `TaskGroup` esperando que todo termine) no funcionan o se cuelgan.
8. Hereda de `BaseException` (lo confirma el `__mro__`) para que un `except Exception:` genérico, que hay por todos lados para manejar errores, **no la atrape sin querer**. La cancelación no es un error de la operación: es una orden de afuera para que pare. Pasa lo mismo con `KeyboardInterrupt` y `SystemExit`.

### Ejercicio 6

1. La tabla:

   | clientes | ok | tiempo | threads |
   |---:|---:|---:|---:|
   | 100 | 100 | 0.06 s | 1 |
   | 500 | 500 | 0.21 s | 1 |
   | 1000 | 1000 | 0.41 s | 1 |
   | 2000 | 2000 | 0.86 s | 1 |
   | 5000 | 5000 | 2.41 s | 1 |
   | 10000 | 10000 | 5.44 s | 1 |
   | 15000 | 15000 | 9.80 s | 1 (con 1154 errores `EMFILE` en `accept`, reintentados) |
   | 20000 | — | se cuelga | 1 (lluvia de `Too many open files`) |

   El proceso usa **1 thread** siempre.
2. Hasta unos **10 000** clientes simultáneos anduvo limpio. Arriba de eso, lo primero que falla son los **descriptores de archivo** (`OSError: [Errno 24] Too many open files` en `accept()`), no la memoria ni la CPU: la máquina tenía 7 GB libres.
3. Sí, se relaciona directamente. `ulimit -n` era 20000, y como cliente y servidor están en el mismo proceso, cada conexión ocupa **2 fds**: 20000 / 2 = 10 000 conexiones. Con `ulimit -n 1024`, 500 anduvo bien, 1000 tardó 9.5 s entre reintentos de `accept` y 2000 se colgó.
4. 10 000 clientes como threads × 4 MB de stack = **~40 GB** de stack virtual, sin contar el costo de que el kernel planifique 10 000 threads. Con asyncio, el mismo proceso hizo todo en un hilo.
5. En la clase 14 cada cliente era un thread o un proceso: memoria de stack por cliente, cambios de contexto del kernel y un techo de unos pocos miles. Con asyncio, en mi máquina un solo hilo atendió **10 000 clientes en 5.4 s** (y 15 000 con reintentos), y el límite fue `ulimit -n`, no el modelo de concurrencia. Cada cliente es una `Task` de unos pocos KB, y esperar I/O no consume un hilo: el loop le pregunta al kernel (epoll) cuáles de los miles de sockets están listos y atiende solo esos. Eso resuelve C10K: el costo por conexión inactiva es casi cero, y el techo pasa a ser un parámetro de configuración (fds), que se sube con `ulimit`.

### Adicionales

- **Chat:** la versión asyncio es más legible. Cada cliente es un bucle lineal (`while linea := await reader.readline()`), sin máquina de estados ni buffers de salida manejados a mano (`salida[conn]`, `sel.modify(... EVENT_WRITE)`): `write()` ya bufferiza y `drain()` hace el control de flujo. Sigue sin hacer falta un lock sobre `clientes`, porque es un solo hilo, pero hay que iterar sobre una copia (`list(clientes)`), porque entre `await`s alguien puede conectarse o irse. Hay un costo: en `difundir`, el `drain()` de un cliente muy lento frena al que mandó el mensaje. La versión con selectors no tenía ese problema porque nunca esperaba.
- **Comandos:** ya **no hace falta el `Lock`**. `conexiones += 1`, `activos.add()` y la lectura para `QUIEN` no tienen ningún `await` en el medio, así que son atómicas. Además desaparecen `setup()` y `finish()` (son el principio de la corrutina y el `finally`) y el estado vive en variables del módulo en vez de en el servidor.
- **Proxy:** usa dos tareas por conexión (`bombear` en cada sentido) y `asyncio.wait(FIRST_COMPLETED)`. Si la que terminó falló, la otra se cancela enseguida. Si terminó por EOF limpio (half-close, como `nc -q 1`), primero propaga el EOF con `write_eof()` y le da a la otra dirección hasta 10 s para terminar de mandar la respuesta. Sin ese detalle, cancelar enseguida cortaba la respuesta del eco: lo vi en la primera versión.
