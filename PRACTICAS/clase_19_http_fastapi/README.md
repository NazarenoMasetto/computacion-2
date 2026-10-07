# Clase 19: HTTP + FastAPI

## Instalación

```bash
python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt
```

`crudo.py`, `cliente_http.py` y `keepalive.py` usan solo la biblioteca estándar.

## Ejercicios → archivos → comandos

Todos los servidores usan el puerto de la consigna y aceptan otro por argumento o por la variable `PUERTO`.

| Ejercicio | Archivo(s) | Comandos |
|---|---|---|
| 1. El protocolo a mano | (respuestas) | `printf 'GET / HTTP/1.1\r\nHost: example.com\r\nConnection: close\r\n\r\n' \| nc example.com 80` (ver la nota sobre la red) |
| 2. http.server es socketserver | `crudo.py` (le agregué `do_DELETE` → 204, el puerto configurable y `--http11`) | `python3 crudo.py` · `python3 crudo.py servidor` · `curl localhost:8080/hola` · `curl -X POST localhost:8080/ -d 'algo'` · `curl -i -X DELETE localhost:8080/x` · `curl -i -X PATCH localhost:8080/x` |
| 3. API con FastAPI (**obligatorio**) | `api.py` (PATCH, /estadisticas, límite de 10 pendientes con 409, `print` de validación, middleware X-Tiempo) | `python3 api.py` → `http://localhost:8000/docs` y los curl de abajo |
| 3 D. Los tipos importan | `ej3d_tipos.py` (las variantes "sin `: int`" y "`prioridad: str`" lado a lado, sin romper `api.py`) | `python3 ej3d_tipos.py` · `curl localhost:8000/sin-tipo/abc` · `curl -X POST localhost:8000/prioridad-str -H 'Content-Type: application/json' -d '{"prioridad":"alta"}'` |
| 4. Dónde está el event loop | `api.py` | `curl localhost:8000/quien-soy` (2 veces) · `curl localhost:8000/quien-soy-sync` · `uvicorn api:app --workers 3` |
| 5. async bien y mal | `medir.py` (le agregué `/hash-async`, `/hash-sync`, `/hash-proceso`), `ej5_datos.py` (el `/datos` mal y los dos arreglos) | `python3 medir.py` · `python3 ej5_datos.py` |
| Adicional: cliente HTTP a mano | `cliente_http.py` | `python3 cliente_http.py http://localhost:8080/hola` |
| Adicional: keep-alive | `keepalive.py` + `crudo.py --http11` | `python3 crudo.py servidor --http11` y en otra terminal `python3 keepalive.py` |
| Adicional: middleware | `api.py` (`medir_tiempo`) | `curl -i localhost:8000/tareas` → header `x-tiempo` |
| Adicional: esqueleto del TP2 | — | **Salteado**: es parte de la entrega del TP2. |

### Verificación del ejercicio obligatorio (ejercicio 3)

```bash
python3 api.py
# los cuatro errores
curl localhost:8000/tareas/abc
curl -X POST localhost:8000/tareas -H 'Content-Type: application/json' -d '{"tipo":"volar"}'
curl -X POST localhost:8000/tareas -H 'Content-Type: application/json' -d '{"tipo":"esperar","prioridad":99}'
curl localhost:8000/tareas/999
# lo agregado
curl -X POST localhost:8000/tareas -H 'Content-Type: application/json' -d '{"tipo":"descargar","prioridad":3}'
curl -X PATCH localhost:8000/tareas/1 -H 'Content-Type: application/json' -d '{"estado":"completada"}'
curl localhost:8000/estadisticas
for i in $(seq 11); do curl -s -o /dev/null -w '%{http_code} ' -X POST localhost:8000/tareas -H 'Content-Type: application/json' -d '{"tipo":"esperar"}'; done
```

Lo que dio cuando lo corrí:

| Pedido | Código | Mensaje |
|---|---|---|
| `GET /tareas/abc` | 422 | `int_parsing`, `loc: ["path","tarea_id"]`, "Input should be a valid integer, unable to parse string as an integer" |
| `POST {"tipo":"volar"}` | 422 | `literal_error`, `loc: ["body","tipo"]`, "Input should be 'descargar', 'hashear' or 'esperar'" |
| `POST {"tipo":"esperar","prioridad":99}` | 422 | `less_than_equal`, `loc: ["body","prioridad"]`, "Input should be less than or equal to 5" |
| `GET /tareas/999` | 404 | `{"detail":"No existe esa tarea"}` |
| `PATCH /tareas/1 {"estado":"completada"}` | 200 | la tarea con `estado: completada` (el resto de los campos no cambia) |
| `PATCH /tareas/1 {"estado":"rota"}` | 422 | `literal_error` en `["body","estado"]` |
| `GET /estadisticas` | 200 | `{"total":11,"por_estado":{"pendiente":10,"ejecutando":0,"completada":1}}` |
| POST número 11 con 10 pendientes | 409 | `{"detail":"Ya hay 10 tareas pendientes (máximo 10)"}` |

- [x] La API levanta y `/docs` responde 200.
- [x] Provoqué los cuatro errores y anoté el código y el mensaje (tabla de arriba).
- [x] Diferencia entre 422 y 404: punto 3.5.
- [x] La validación ocurre antes de la función: el `print('[crear] ...')` sale solo con los POST válidos. Con `volar` y con `99` no se imprime nada.
- [x] `PATCH /tareas/{id}` con el modelo `TareaParcial` (todos los campos opcionales, `model_dump(exclude_unset=True)`).
- [x] `GET /estadisticas`.
- [x] Código para el límite de pendientes: 409 (justificado en el punto 3.10).
- [x] Qué hace FastAPI con las anotaciones: punto 3.13.

## Qué se probó

- **Sin salida a internet:** `example.com` está bloqueado por el proxy del entorno (`nc example.com 80` devuelve un `403 Forbidden` del proxy, `x-deny-reason: host_not_allowed`). El ejercicio 1 lo probé contra servidores locales (uvicorn con `api.py` y `crudo.py`). Las respuestas sobre `example.com` son teóricas.
- `crudo.py`: la demo completa, GET, POST, DELETE (204), PATCH (501), pedido con `\n` solo y pedido sin `Host`.
- `api.py`: `/docs`, `/openapi.json`, los cuatro errores, PATCH (válido, inválido y vacío), el límite con 409, `/estadisticas`, DELETE, `/quien-soy` (2 veces), `/quien-soy-sync`, `--workers 3` (3 pids distintos; la tarea recién creada dio `200 200 404 404 ...`), el header `x-tiempo`.
- `ej3d_tipos.py`: las variantes con y sin tipo, con prioridad `int` y `str`.
- `medir.py` y `ej5_datos.py`: medidos (los números están en las respuestas).
- `cliente_http.py`: contra `crudo.py` (Content-Length), contra un `nc -l` que responde sin Content-Length (lee hasta el cierre) y contra un `StreamingResponse` de uvicorn (chunked).
- `keepalive.py`: contra `crudo.py` en HTTP/1.0 (la conexión se cierra después de la primera respuesta) y con `--http11` (las dos respuestas, y una tercera, por la misma conexión).
- Lo que no probé: `/docs` en un navegador (solo comprobé que responde 200 y que `openapi.json` se genera) ni el "Try it out".

## Respuestas

### Ejercicio 1

1. Las tres partes son la línea de estado (`HTTP/1.1 200 OK`), los headers (`Nombre: valor`, uno por línea) y el cuerpo. Cada línea termina en `\r\n`, y los headers se separan del cuerpo con una línea vacía (`\r\n\r\n`).
2. `200 OK`, de la familia 2xx (salió bien). Contra el servidor local también dio 200.
3. Sin `Host:`, un servidor que cumple HTTP/1.1 responde `400 Bad Request`. Lo comprobé con uvicorn: `HTTP/1.1 400 Bad Request ... Invalid HTTP request received.`. `crudo.py` igual responde 200, porque `http.server` no lo controla. HTTP/1.1 lo exige porque muchos sitios comparten una misma IP (virtual hosting), y `Host` es lo único que le dice al servidor cuál de esos sitios le estás pidiendo.
4. `404 Not Found`, si el recurso no existe. Uvicorn dio 404. `crudo.py` responde 200 a cualquier ruta, porque su `do_GET` no mira el path.
5. Con `\n` solo: `crudo.py` lo acepta (`http.server` lee con `readline()` y hace strip de `\r\n`), y uvicorn (h11) también respondió 200. Contra `example.com` no lo pude probar por el bloqueo de red. Hoy la mayoría de los servidores grandes lo toleran, pero la RFC exige CRLF y no está garantizado.
6. Porque es comportamiento no especificado: otro servidor, un proxy o una versión nueva más estricta pueden rechazarlo o, peor, interpretar distinto dónde terminan los headers (de ahí salen ataques como el request smuggling). Hay que mandar lo que dice la especificación.
7. Seguros: `GET` y `HEAD`. `POST`, `PUT` y `DELETE` modifican.
8. Idempotentes: `GET`, `HEAD`, `PUT` y `DELETE`. `POST` no lo es porque cada ejecución crea un recurso nuevo: dos POST iguales dan dos tareas con ids distintos. En cambio, dos `PUT` dejan el recurso en el mismo estado y dos `DELETE` dejan el recurso borrado.
9. Reintentar un `POST` **no** es seguro: puede ser que el servidor lo haya procesado y lo que se perdió fue la respuesta, y entonces lo duplicás. Un `PUT` sí se puede reintentar sin problema, porque es idempotente.
10. Es el mismo problema que en UDP: sin confirmación no sabés si se perdió el pedido o la respuesta. Si reintentás, el receptor puede recibirlo dos veces. La solución también es la misma: hacer la operación idempotente o mandar un identificador único (un número de secuencia en UDP, una `Idempotency-Key` en HTTP) para que el servidor detecte el duplicado y lo descarte.

### Ejercicio 2

1. `BaseHTTPRequestHandler` hereda de `socketserver.StreamRequestHandler`. Le aporta el `handle()` llamado por el servidor y los `rfile`/`wfile` (el socket como archivo, con `readline()`), que son justo lo que hace falta para leer líneas de headers y `n` bytes de cuerpo.
2. `ThreadingHTTPServer` usa `ThreadingMixIn` + `HTTPServer` (que es un `TCPServer`). Es el mismo mixin de la clase 16: un thread por conexión.
3. Porque TCP es un flujo sin límites de mensaje. `recv(4096)` puede traer medio cuerpo, o el cuerpo más el principio del pedido siguiente (keep-alive). `Content-Length` es el framing por longitud: hay que leer exactamente esos bytes, ni uno más ni uno menos.
4. Con `protocol_version = 'HTTP/1.1'` el servidor responde `HTTP/1.1` y **no cierra la conexión** después de responder (keep-alive), salvo que venga `Connection: close`. A cambio, siempre hay que mandar `Content-Length` (o chunked), porque el cliente ya no puede usar el cierre para saber dónde termina el cuerpo. Lo probé con `keepalive.py`.
5. Agregué `do_DELETE` y responde `204 No Content`: el borrado salió bien y no hay nada que devolver. También sirve `200` con un cuerpo de confirmación, o `202` si el borrado fuera diferido.
6. Con `PATCH`, que no está implementado, el framework solo responde `501 Unsupported method ('PATCH')` (501 Not Implemented), con una página HTML de error.
7. En `crudo.py`, un endpoint necesita unas 7 u 8 líneas: el `do_GET`, `json.dumps`, `send_response`, dos `send_header` (Content-Type y Content-Length), `end_headers` y `wfile.write`. Por eso está factorizado en `_responder`. Además, un `do_GET` atiende todas las rutas, así que el ruteo es a mano. En `api.py` son 3 líneas: el decorador, el `def` y el `return` de un dict. El ruteo, el JSON, los headers y la validación los pone el framework.

### Ejercicio 3

1. Nadie la escribió a mano. FastAPI la genera sola a partir de las rutas, las anotaciones de tipo, los modelos Pydantic y los docstrings. La interfaz es Swagger UI.
2. Con un `tipo` fuera de la lista, la respuesta es 422 con `literal_error`. Swagger además muestra un desplegable con los tres valores válidos, porque `Literal` se documenta como `enum`.
3. `openapi.json` es la especificación OpenAPI 3.1 de la API: un JSON estándar que describe todos los endpoints, parámetros, modelos y respuestas. `/docs` se dibuja a partir de ese archivo, y sirve también para generar clientes automáticamente en otros lenguajes.
4. Ver la tabla de la verificación.
5. Los tres primeros dan **422** y `/tareas/999` da **404**. El 422 significa que el pedido está mal en sí mismo (un tipo o un valor inválido) y lo detecta la validación antes de ejecutar tu código. El 404 significa que el pedido es válido (999 es un int), pero el recurso no existe, y eso solo se sabe ejecutando la función y mirando los datos.
6. `loc` dice **dónde** está el error: primero la parte del pedido (`path`, `query`, `body`, `header`) y después el campo (`tarea_id`, `prioridad`...). Con eso el cliente sabe exactamente qué corregir.
7. **Antes.** Puse un `print` al principio de `crear()`: con los POST válidos se imprime y con `volar` o `99` no aparece nada en el log, aunque el cliente recibe el 422. La función nunca llega a ejecutarse.
8. Lo implementé con el modelo `TareaParcial`, donde `estado: Estado | None = None`, y `model_dump(exclude_unset=True)` aplica solo lo que mandó el cliente. Un PATCH con `{}` no cambia nada.
9. Lo implementé: `{"total": N, "por_estado": {"pendiente": .., "ejecutando": .., "completada": ..}}`.
10. Elegí **409 Conflict**: el pedido está bien formado y es válido (no corresponde 422), pero choca con el estado actual del servidor (la cola ya tiene 10 pendientes). Si después se completan tareas, el mismo pedido va a andar. Las alternativas razonables son `429 Too Many Requests`, aunque ese código está más pensado para limitar la tasa de un cliente que para una cola llena, y `503 Service Unavailable` (con `Retry-After`), aunque ese tira la culpa al servidor (5xx). Descarté 400 y 422 porque los datos no tienen nada de malo.
11. Sin `: int`, FastAPI trata el parámetro como `str`, y entonces no valida ni convierte. `/tareas/abc` ya no da 422: entra a la función y da **404**. Peor todavía, `/tareas/1` **también da 404**, porque `"1"` (str) no está en el dict, que tiene claves int. Lo probé con `/sin-tipo/1` en `ej3d_tipos.py`. Además `/docs` deja de mostrar que el parámetro es entero.
12. Con `prioridad: str` acepta cualquier string: `"3"`, `"alta"`, `""`. Rechaza los números JSON (`3`, `99`, `3.0` dan 422 `string_type`), porque Pydantic v2 no convierte de int a str. Se pierden la conversión a número y el rango 1 a 5. Si dejás el `Field(ge=1, le=5)` con `str`, la validación revienta con `TypeError` (un 500), porque no puede comparar un string con 1.
13. Con cada anotación hace tres cosas: **valida** (y responde 422 si no cumple), **convierte** (por ejemplo el string `"42"` de la URL a `int` 42) y **documenta** (OpenAPI y `/docs`). La serialización de la respuesta con `response_model` sale del mismo mecanismo.

### Ejercicio 4

1. El `async def` corre en `MainThread`, el hilo del event loop. El `def` común corre en un `AnyIO worker thread` (el threadpool).
2. El `id_del_loop` fue el mismo en los dos pedidos (`_UnixSelectorEventLoop`, mismo pid): hay **un solo** event loop por proceso.
3. Porque corre en un thread del threadpool, y el event loop existe solo en el hilo principal: `get_running_loop()` busca el loop del thread actual y en ese thread no hay ninguno.
4. Lo crea **uvicorn**. FastAPI es solo la aplicación que uvicorn invoca. ASGI (Asynchronous Server Gateway Interface) es la especificación que define cómo un servidor asíncrono le pasa los pedidos a una aplicación: `app(scope, receive, send)`.
5. Sí. Con `--workers 3`, en 8 pedidos vi 3 pids distintos (4, 2 y 2 pedidos). Son tres procesos, cada uno con su loop.
6. Creé la tarea 1 y después la pedí 12 veces: `200 200 404 404 404 ...`. El diccionario `tareas` existe en el proceso que atendió el POST. Los otros dos workers tienen su propia copia vacía, porque los procesos no comparten memoria, y según a qué worker te toque la conexión la tarea existe o no.
7. Con más de un worker, el estado no puede vivir en una variable global. En un sistema real va afuera de los procesos de la API: una base de datos, Redis, una cola de mensajes. Si no, hay que correr un solo worker y aceptar que el estado se pierde al reiniciar.

### Ejercicio 5

1. Los tiempos que me dio: `/async-bien 1.03s`, `/async-mal 3.01s`, `/sync 1.04s` (3 pedidos de 1 s).
2. `time.sleep` dentro de `async def` no cede el control: bloquea el único event loop, así que los 3 pedidos se atienden uno detrás del otro (3 × 1 s). Es la regla de la clase 18: dentro de una corrutina nunca hay que llamar a algo bloqueante. Solo se espera con `await`.
3. Porque FastAPI ve que es un `def` común y lo corre en el threadpool. Cada pedido bloquea su propio thread, no el loop, y los 3 sleeps se solapan.
4. La regla: **`async def` solo si todo lo lento que hace es con `await` sobre bibliotecas async; si usa algo bloqueante (requests, una DB sincrónica, `time.sleep`), `def` común; si es CPU pesado, `def` o, mejor, un executor de procesos.** Un `def` es mejor que un `async def` mal escrito.
5. Está **mal**: `requests.get` es bloqueante y está adentro de `async def`, así que congela el loop mientras espera la red. Medido con `ej5_datos.py` (el remoto tarda 1 s): `/datos-mal` → 3.07 s para 3 pedidos. Un detalle menor: el `import` adentro de la función no rompe nada, pero se ejecuta en cada pedido.
6. Los dos arreglos están en `ej5_datos.py`. (a) Pasarlo a `def` y seguir con `requests`: va al threadpool y tarda 1.05 s. (b) Dejar `async def` y cambiar a `httpx.AsyncClient` con `await`: tarda 1.27 s. Lo ideal sería crear el `AsyncClient` una vez y reutilizarlo; en el ejemplo se crea por pedido para que quede corto.
7. Agregué el hash iterado (sha256 un millón de veces, alrededor de 1 s) en tres formas. Con 3 pedidos y 2 cores: `/hash-async 2.55s`, `/hash-sync 3.05s`, `/hash-proceso 1.93s`. `async def` congela el loop. `def` no congela el loop (otros endpoints siguen respondiendo), pero los threads se pelean el GIL y no tarda menos. La única forma que escala es `run_in_executor` con un `ProcessPoolExecutor`: otro proceso, otro GIL, otro core. Con 2 cores, 3 tareas se hacen en unas 2 rondas. De las tres formas originales ninguna lo resuelve bien. La menos mala es `def`, porque al menos no bloquea a los demás pedidos.

### Adicionales

- **Keep-alive:** sabés dónde termina la primera respuesta por el **framing**: los headers terminan en la línea vacía y el cuerpo mide exactamente `Content-Length` bytes (o termina en el chunk de tamaño 0 si es chunked). Lo que sigue en el flujo es la segunda respuesta. Con HTTP/1.0 el servidor cierra después de la primera y la segunda nunca llega (lo muestra `keepalive.py`).
- **Middleware:** `@app.middleware('http')` envuelve a **todos** los endpoints. El código antes de `await call_next(request)` corre antes del endpoint (y antes de la validación), y el código de después corre cuando el endpoint ya devolvió la respuesta. Por eso puede medir el tiempo total y agregar `X-Tiempo` a la respuesta. También envuelve los 422 y los 404.
