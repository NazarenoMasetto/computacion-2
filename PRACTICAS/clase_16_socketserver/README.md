# Clase 16 — socketserver

Python 3.10+ (probado con 3.13 en Linux), solo stdlib. Todos los servidores usan el puerto **8080** por defecto y aceptan `--port N`.
En las pruebas usé puertos 29000-29099 para no chocar con otros servicios.

## Archivos y cómo correrlos

| Ejercicio | Archivo(s) | Terminal 1 (servidor) | Terminal 2 (cliente) |
|---|---|---|---|
| 1.1 mínimo | `ej1_progresion.py` | `python3 ej1_progresion.py --paso minimo` | `nc localhost 8080` (3 veces) |
| 1.2 puerto ocupado | `ej1_progresion.py` | `python3 ej1_progresion.py` → conectar → Ctrl+C → relanzar; después igual con `--reuse` | `nc localhost 8080` |
| 1.3 concurrencia | `ej1_progresion.py`, `cliente_medir.py` | `python3 ej1_progresion.py --paso lento --servidor secuencial` (o `threading` / `forking`) | `python3 cliente_medir.py -n 2` |
| 1.4 framing | `ej1_progresion.py` | `python3 ej1_progresion.py --paso recv` (o `--paso stream`) | `printf 'UNO\nDOS\n' \| nc -q1 localhost 8080` |
| 1.5 estado | `ej1_progresion.py`, `cliente_medir.py` | `python3 ej1_progresion.py --paso contador-handler` / `--paso contador-servidor --servidor threading` / `--paso contador-sinlock --servidor threading` | `nc -q1 localhost 8080 </dev/null` (x3) y `python3 cliente_medir.py -n 200 --resumen` |
| 1.6 errores | `ej1_progresion.py` | `python3 ej1_progresion.py --paso errores` (y con `--sin-super`) | `printf 'hola\nCRASH\n' \| nc -q1 localhost 8080` |
| 2 A/B mixins | `ej2_mixins.py` | `python3 ej2_mixins.py` (análisis) / `python3 ej2_mixins.py --servir bien` (o `mal`) | `python3 cliente_medir.py -n 2` |
| 2 C forking | `ej2_forking_value.py` | `python3 ej2_forking_value.py` y `python3 ej2_forking_value.py --value` | `nc -q1 localhost 8080 </dev/null` (x3) |
| 2 D daemon | `ej2_daemon.py` | `python3 ej2_daemon.py --sin-daemon` (y sin la opción), Ctrl+C con el cliente abierto | `nc localhost 8080` (dejarlo abierto) |
| 3 UDP | `ej3_udp.py` | `python3 ej3_udp.py` / `--files` / `--lento` / `--lento --threading` | `echo hola \| nc -u -w1 localhost 8080` o `python3 ej3_udp.py --cliente hola -n 3` |
| 4 servidor de verdad | `comandos.py` | `python3 comandos.py [--timeout 30]` | `nc localhost 8080` (dos terminales: `NICK ana`, `QUIEN`, `BROADCAST hola`) |
| 5 el límite | `comandos.sh`, `ej5_conexiones.py` | `bash comandos.sh` (levanta el servidor y mide solo) | — |
| Adicional: archivos | `servidor_archivos.py` | `python3 servidor_archivos.py --dir .` | `python3 servidor_archivos.py --get comandos.sh` / `--get noexiste` |
| Adicional: chat | `chat_socketserver.py` | `python3 chat_socketserver.py` | `nc localhost 8080` en varias terminales |
| Adicional: timeout | `timeout_inactividad.py` | `python3 timeout_inactividad.py --timeout 10` | `nc localhost 8080` y no escribir |
| Adicional: comparar / leer fuente | (respuestas abajo) | — | — |

`cliente_medir.py` es un cliente auxiliar: abre N conexiones simultáneas, manda una línea y mide cuánto tarda cada respuesta.

## Qué se probó

Todo se corrió en Linux con Python 3.13, servidores en background y clientes con `timeout`:

- 1.1 a 1.6: todos los `--paso`, con las tres variantes de servidor. Los números de abajo son de esas corridas.
- 2: análisis de los mixins, `bien`/`mal` medidos, el contador con forking con y sin `Value`, y `daemon_threads` midiendo cuánto tarda en cerrar.
- 3: los cuatro modos con `nc -u` y con el cliente de 3 datagramas.
- 4: un script con dos clientes: NICK, QUIEN, BROADCAST, el cliente B que se va de golpe y el timeout (con `--timeout 2`).
- 5: `comandos.sh` completo.
- Adicionales: archivo existente, inexistente y `../../../etc/passwd`, el chat con 2 clientes y el timeout.

## Respuestas

### Ejercicio 1

1. `self.request` es el socket **conectado** con ese cliente (el que devuelve `accept()`). Imprime `<class 'socket.socket'>`.
2. Cada conexión crea un handler nuevo. En la prueba salieron ids distintos, aunque a veces se repite uno: CPython reutiliza la dirección de memoria de un objeto que ya se liberó. Lo que no se repite nunca es el objeto vivo.
3. `handle()` corre **una sola vez por conexión**. Con tres mensajes en la misma conexión, el bucle `recv()` de adentro da tres vueltas y `handle()` se ejecuta una vez.
4. `OSError: [Errno 98] Address already in use`. Lo reproduje cortando el servidor mientras el cliente seguía conectado: el servidor cierra primero y su lado queda en FIN_WAIT/TIME_WAIT.
5. Si nunca se conectó nadie, relanza sin error. TIME_WAIT lo genera el lado que cierra primero una conexión **establecida**. Sin conexiones no hay nada en TIME_WAIT y el puerto queda libre.
6. Con `--reuse` (`allow_reuse_address = True`) relanza bien. Ojo: en Linux tienen que haber tenido SO_REUSEADDR **los dos**, el servidor viejo y el nuevo. Si el viejo corría sin `--reuse`, el nuevo falla igual.
7. Secuencial: cliente 1 → 3,0 s y cliente 2 → **6,0 s**. Total 6,0 s.
8. `ThreadingTCPServer`: **3,0 s y 3,0 s**. Total 3,0 s.
9. `ForkingTCPServer`: también 3,0 s. Aparecen **2 PIDs distintos en el handler**, uno por cliente, más el del padre (3 en total).
10. Con `recv(1024)` el servidor recibe `b'UNO\nDOS\n'` de una y responde una sola vez (`recibi: UNO\nDOS`).
11. Con `StreamRequestHandler` se itera `rfile` y llegan dos líneas, `b'UNO\n'` y `b'DOS\n'`, con dos respuestas.
12. `rfile` tiene buffer propio y le saca al socket más bytes de los que pediste. Un `recv()` después espera datos que ya están en ese buffer y el handler **se cuelga** sin dar error.
13. Siempre da `visita 1`. `self.n += 1` lee el 0 de la clase y guarda 1 en la **instancia**, y la instancia muere con la conexión.
14. Con el contador en el servidor (`self.server.visitas`) sí cuenta: 1, 2, 3. Con 200 conexiones más llegó a 203.
15. Sin el Lock y con 200 conexiones no se perdió ninguna (dio 201 contando la de control). Eso no prueba que esté bien: el `+=` son varias instrucciones de bytecode y el GIL **puede** cambiar de thread en el medio. La ventana es chiquita y no se dio en esta corrida, pero es una race condition igual. Con más carga, otra versión de Python o sin GIL (3.13t) puede aparecer.
16. No, el servidor no se cae. `handle_error()` loguea y sigue: la conexión siguiente se atendió bien.
17. Sí, `finish()` se ejecuta. Orden observado: `setup → handle → finish → handle_error`. `finish()` se llama dentro de `finish_request` (en el `finally` del handler) y la excepción le llega a `handle_error()` después.
18. Sin `super().setup()` no se crean `rfile`/`wfile` y salta `AttributeError: 'ConErrores' object has no attribute 'rfile'` en `handle()`. Además `finish()` no tiene nada que flushear.

### Ejercicio 2 (obligatorio)

**Parte A**
1. `ThreadingMixIn` define 3 métodos: `process_request_thread`, `process_request` y `server_close`. La concurrencia la produce **`process_request`**, que crea y arranca un `Thread` por conexión.
2. El de `BaseServer` llama a `finish_request()` y `shutdown_request()` **en el mismo hilo**: bloquea hasta que termina el handler. El del mixin hace lo mismo pero dentro de un thread nuevo y vuelve enseguida al bucle.
3. `ForkingMixIn` cosecha en `collect_children()`, que hace `waitpid(..., WNOHANG)` sobre `active_children`. Se llama desde `service_actions()`, en **cada vuelta de `serve_forever()`** (como mucho cada 0,5 s), desde `handle_timeout()` y en `server_close()`. Por eso no quedan zombies: alguien hace `wait()` seguido, sin que lo programemos.
4. Ninguno: `class ThreadingTCPServer(ThreadingMixIn, TCPServer): pass`.

**Parte B**
5. `Bien`: `Bien → ThreadingMixIn → TCPServer → BaseServer`. `Mal`: `Mal → TCPServer → BaseServer → ThreadingMixIn`. En `Mal` el mixin queda **después** de `BaseServer`.
6. En `Bien`, `process_request` lo provee `ThreadingMixIn`. En `Mal` lo provee `BaseServer`: el del mixin queda tapado.
7. `Bien`: 3,0 s y 3,0 s (paralelo). `Mal`: 3,0 s y **6,0 s** (secuencial).
8. `Mal` no da ningún error: arranca y responde. Es peligroso porque pasa las pruebas con un cliente y el problema aparece recién con carga, como "el servidor está lento", sin un traceback que lo explique.

**Parte C**
9. Con `ForkingTCPServer` y un int, siempre `visita 1`, y cada respuesta sale de un PID distinto.
10. `fork()` le da al hijo una **copia** de la memoria del padre (copy-on-write). El hijo incrementa su copia y se muere, y el padre sigue con 0. No es un problema de sincronización sino de aislamiento.
11. Memoria compartida: `multiprocessing.Value('i', 0)` con su `get_lock()` (`ej2_forking_value.py --value`). Resultado: `visita 1, 2, 3` desde PIDs distintos.
12. En el **`__init__` del servidor**, o sea en el padre y antes de cualquier fork, para que todos los hijos hereden el mismo segmento compartido. Si se creara en el handler, cada hijo tendría su propio `Value` nuevo.

**Parte D**
13. Sin `daemon_threads`, el Ctrl+C no termina el proceso: `server_close()` hace `join()` de los threads no daemon y se queda esperando que el cliente cierre. En la prueba tardó 5,5 s, justo lo que tardó el `nc` en morir.
14. Con `daemon_threads = True` cerró en 0,01 s. Los threads daemon no se registran para el `join` y mueren con el proceso.

### Ejercicio 3

1. `self.request` es una **tupla** `(datos, socket)`: `<class 'tuple'>`.
2. El socket UDP del servidor no está conectado a nadie: es uno solo para todos los clientes. Por eso el destino va explícito en cada `sendto()`. En TCP, el socket de `accept()` ya está atado a un cliente.
3. `DatagramRequestHandler` esconde el desempaquetado de la tupla. Arma `rfile` con los datos recibidos y `wfile` como buffer, y en `finish()` hace el `sendto(..., client_address)` solo.
4. Sí, `ThreadingUDPServer` existe y tiene sentido. No hay conexiones, pero cada datagrama es una "petición", y si el handler tarda bloquea a los siguientes. Con un handler de 2 s y 3 datagramas: `UDPServer` respondió a los 2, 4 y 6 s, y `ThreadingUDPServer` los tres a los 2 s.

### Ejercicio 4

1. `NICK`: el apodo es de **esa conexión**, así que vive en el handler (`self.nick`), que dura lo mismo que la conexión. Pero otros clientes lo necesitan ver (QUIEN, BROADCAST), así que el servidor guarda en `self.server.clientes` una referencia a cada handler, protegida con el lock. Si estuviera solo en el servidor, habría que limpiarlo a mano al desconectar. Si estuviera solo en el handler, nadie más lo vería.
2. `BROADCAST`: se recorre una **copia** de `server.clientes` (tomada con el lock) y se escribe en el `wfile` de cada handler, es decir en su socket. Cada handler tiene un `lock_escritura` para que no se mezclen líneas cuando dos threads le escriben al mismo cliente.
3. Si un cliente se va mientras otro le escribe, `write()` lanza `BrokenPipeError`/`ConnectionResetError`. `responder()` lo atrapa y devuelve `False`, el broadcast sigue con los demás, y el handler del que se fue se saca de la lista en su `finish()`. Probado: después de que B se fue, el broadcast de A dijo "enviado a 1 clientes" y el servidor siguió andando.
4. Timeout: `Handler.timeout = 30` (configurable con `--timeout`). `StreamRequestHandler.setup()` hace `settimeout()` y, si el cliente no manda nada, `rfile` lanza `TimeoutError`. Lo atrapo, aviso "Desconectado por inactividad" y cierro. Probado con 2 s.
5. Con `ForkingTCPServer` el `BROADCAST` **no funcionaría**. Cada cliente está en otro proceso y `server.clientes` es una copia distinta en cada hijo (el padre ni siquiera ejecuta handlers). Además los sockets de los otros clientes no existen en ese proceso. Haría falta IPC.

### Ejercicio 5

Resultados de `comandos.sh`:

| Situación | Threads | RSS |
|---|---|---|
| En reposo | 1 | 12,8 MB |
| 200 conexiones | 201 | 18,2 MB |
| 1000 conexiones | 1001 | 39,0 MB |
| Después de cerrar todo | 1 | 21,1 MB |

1-3. Con 200 conexiones hay 201 threads: **un thread por conexión** más el principal.
4. Con 1000 también anduvo (1001 threads, unos 26 KB de RSS por thread). En esta máquina `ulimit -n` es 20000. Con el default típico de 1024, cerca de las 1000 conexiones empieza a fallar `accept()` con "Too many open files". Además cada thread reserva 8 MB de stack **virtual**, el scheduler tiene que repartir CPU entre mil threads y el GIL se vuelve el cuello de botella.
5. No. `socketserver` **no resuelve C10K**: es el mismo modelo de un thread (o proceso) por cliente de la clase 14, solo que escrito más prolijo. La memoria y los threads crecen linealmente con las conexiones (con 10000 serían unos 10000 threads), aunque casi todas estén ociosas. Para eso hace falta multiplexing (clase 17).

### Adicionales

- **Servidor de archivos**: protocolo `GET <nombre>\n` → cabecera `!BI` (estado, largo) + bytes. Si el archivo no existe responde estado 1 con el error y el servidor sigue. También rechaza rutas fuera de `--dir` (`../../../etc/passwd` → "acceso denegado").
- **Chat con socketserver**: la versión con threads es **más simple de leer**. No hay buffers de salida, ni `EVENT_WRITE`, ni framing manual (`rfile` da líneas), y cada handler es un bucle lineal. El precio es el lock sobre la lista de clientes, un thread por usuario y que un cliente lento bloquee al thread del que le escribe. La de `selectors` escala mejor pero tiene más maquinaria.
- **Timeout de inactividad**: `timeout_inactividad.py`. Con `--timeout 1.5`, al cliente que no escribe le llega "Desconectado por inactividad" y en el servidor se loguea `handle_timeout()`.
- **Comparar con la clase 14**: `server_threads.py` tiene 68 líneas (53 de código) y `eco_tcp.py` tiene 62 (41 de código). Pero `eco_tcp.py` además ofrece modo fork y MRO impreso: el eco en sí son unas 12 líneas.

  | Lo que hay que hacer | Clase 14 (a mano) | socketserver |
  |---|---|---|
  | socket/bind/listen | explícito | `TCPServer.__init__` |
  | SO_REUSEADDR | `setsockopt` | `allow_reuse_address = True` |
  | Bucle de accept | `while True: accept()` | `serve_forever()` |
  | Un thread por cliente | `Thread(...).start()` | `ThreadingMixIn` |
  | Threads daemon | `daemon=True` | `daemon_threads = True` |
  | Cosechar hijos (fork) | `waitpid` / SIGCHLD | `collect_children()` |
  | Excepciones del handler | `try/except` propio | `handle_error()` |
  | Cerrar la conexión | `with conn` / `close()` | `shutdown_request()` |
  | Framing por líneas | buffer manual | `rfile`/`wfile` |

- **Leer el fuente**: `serve_forever()` usa `_ServerSelector`, que es `selectors.PollSelector` si existe `poll` (si no, `SelectSelector`). Registra **solo el socket que escucha** y llama a `selector.select(poll_interval)` con un timeout de 0,5 s para poder chequear `shutdown()` y correr `service_actions()`. Es el multiplexing de la clase 17, pero usado sobre un único fd. La concurrencia no sale de ahí sino de los mixins (threads/procesos). Un servidor de la clase 17 registra **todos** los sockets en el selector y no necesita threads.
