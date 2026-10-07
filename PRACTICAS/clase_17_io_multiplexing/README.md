# Clase 17 — I/O Multiplexing

Python 3.10+ (probado con 3.13 en Linux), solo stdlib. Todos los servidores usan el puerto **8080** por defecto y aceptan `--port N`.
En las pruebas usé puertos 29100-29199.

> Nota: el `ejercicios.md` de la cátedra dice "Clase 16" en el título, pero es el de esta carpeta (clase 17).

## Archivos y cómo correrlos

| Ejercicio | Archivo(s) | Terminal 1 (servidor) | Terminal 2 (cliente / medición) |
|---|---|---|---|
| 0 Direcciones | `ej0_direcciones.py` | `python3 ej0_direcciones.py [--v6only]` (todo en una terminal) | — |
| 1.1 Busy-waiting | `ej1_busy_wait.py` | `python3 ej1_busy_wait.py` | `nc localhost 8080`; CPU: `top -p <pid>` o `ps -o %cpu= -p <pid>` |
| 1.1 Comparación | `servidor_select.py` (de la cátedra) | `python3 ../../compu2_um_2026/clase_17_io_multiplexing/servidor_select.py` | ídem |
| 2.1 / 2.2 select | `ej2_servidor_select.py` | `python3 ej2_servidor_select.py` / `--bug` / `--bug-sin-close` | 3 × `nc localhost 8080`; `ls /proc/<pid>/task \| wc -l` |
| 2.3 FD_SETSIZE | `ej2_fdsetsize.py` | `python3 ej2_fdsetsize.py` | — |
| 3 Comparar (obligatorio) | `ej3_comparar.py` | `python3 ej3_comparar.py`; `python3 ej3_comparar.py --activos 0.5`; `python3 ej3_comparar.py 10 50 100` | — |
| 4 selectors | `ej4_servidor_selectors.py` | `python3 ej4_servidor_selectors.py` / `--select-selector` / `--sin-unregister` | `echo hola \| nc -q0 localhost 8080` (varias veces) |
| 5 Escritura | `ej5_escritura.py` | `python3 ej5_escritura.py` / `--write-siempre` | `nc localhost 8080` y mirar el CPU |
| 6 Chat | `chat.py` | `python3 chat.py` | varios `nc localhost 8080`: `/nick ana`, `/lista`, mensajes |
| 7 Hilo único | `ej7_hilo_unico.py` | `python3 ej7_hilo_unico.py` / `--threads` / `--pool` | T2: `echo calcular \| nc -q5 localhost 8080`; T3 enseguida: `echo ping \| nc -q1 localhost 8080` |
| Adicional: timeout | `servidor_timeout.py` | `python3 servidor_timeout.py --timeout 30` | `nc localhost 8080` y no escribir |
| Adicional: proxy | `proxy_tcp.py` | `python3 ej5_escritura.py --port 9000` y `python3 proxy_tcp.py --destino localhost:9000` | `nc localhost 8080` |
| Adicional: techo | `medir_techo.py` | `python3 ej4_servidor_selectors.py` | `python3 medir_techo.py --max 20000` |
| Adicional: self-pipe | `self_pipe.py` | `python3 self_pipe.py` → Ctrl+C | `nc localhost 8080` (ver el mensaje de cierre) |

## Qué se probó

Todo se corrió en Linux con Python 3.13:

- 1.1: CPU del busy-wait contra `select`.
- 2: los tres modos y la cantidad de threads.
- 2.3: el script.
- 3: las tres corridas del benchmark.
- 4: los tres modos.
- 5: CPU con y sin `--write-siempre`.
- 6: script con 2 clientes que prueba `/nick`, `/lista`, media línea y varias líneas juntas, y lo mismo contra el chat original para ver el bug de framing.
- 7: los tres modos con un cliente "calcular" y un "ping".
- Adicionales: timeout, proxy (eco simple y 3 transferencias simultáneas de 5 MB verificadas byte a byte), techo con 9500 conexiones y con `ulimit -n 1024`, y self-pipe con `kill -INT`.

**No se pudo probar:** las partes de IPv6 del ejercicio 0 (0.2 y 0.4). El contenedor no tiene IPv6 (`socket.AF_INET6` da `Errno 97 Address family not supported`) y tampoco tiene `ip` ni Docker. El script lo detecta y lo informa. Las respuestas de esas partes son teóricas.

## Respuestas

### Ejercicio 0

1. `192.168.1.37` está en la red: el sistema lo entrega **directo** en la LAN (ARP para obtener la MAC del destino). `192.168.2.10` no está: el paquete va al **gateway** (router por defecto), con la MAC del router.
2. `docker0` suele ser `172.17.0.1/16`. Los contenedores en la misma red bridge están en la misma subred `172.17.0.0/16`, así que se hablan directo por el bridge sin pasar por un router. No hay que configurar nada.
3. `getsockname()` en IPv6 devuelve **4 elementos**: `('::1', puerto, flowinfo, scope_id)`.
4. `ValueError: too many values to unpack (expected 2)`. La forma portable es `host, puerto = direccion[0], direccion[1]` (o `direccion[:2]`).
5. Porque en IPv4 la tupla tiene exactamente 2 elementos y el desempaquetado anda. Recién falla cuando un cliente llega por IPv6.
6. Devuelve las **dos** familias. Acá salieron primero las 6 IPv4 y después 4 IPv6. El orden lo decide el sistema (RFC 6724 / `gai.conf`); en una máquina con IPv6 funcional suelen salir primero las IPv6.
7. Porque la primera puede no ser alcanzable: si sale una IPv6 y no tenés ruta IPv6, el `connect()` falla. Hay que probar en orden y quedarse con la primera que conecte. En esta máquina, sin IPv6, solo sirven las IPv4.
8. `socket.create_connection()` hace justamente eso: `getaddrinfo` + probar cada dirección en orden con timeout, y devuelve el primer socket conectado (o lanza el último error).
9. *(teórica)* Desde `::1` el servidor ve `::1`. Desde `127.0.0.1` ve `::ffff:127.0.0.1`.
10. El prefijo es `::ffff:` (dirección IPv4 mapeada en IPv6). Importa porque si filtrás por IP comparando contra `'127.0.0.1'` no va a coincidir: hay que normalizar (`ipaddress.ip_address(x).ipv4_mapped`).
11. Con `IPV6_V6ONLY = 1` el socket solo acepta IPv6. El cliente IPv4 recibe **Connection refused**, salvo que haya otro socket IPv4 escuchando en ese puerto.
12. Porque el default depende del sistema (`/proc/sys/net/ipv6/bindv6only` en Linux, y es distinto en BSD/Windows). Si lo dejás implícito, el mismo código se comporta distinto en otra máquina.

### Ejercicio 1

1. Sí, funciona: el eco responde.
2. Con **nadie conectado**: ~**97-100 % de CPU** (un core entero, medido con `ps` y `top`).
3. Porque nunca duerme. El bucle pregunta "¿hay algo?" millones de veces por segundo, cada `accept()`/`recv()` no bloqueante vuelve con `BlockingIOError` y vuelta a empezar. Es *busy-waiting*.
4. `servidor_select.py` en reposo: **0,0-0,2 % de CPU**. `select()` duerme el proceso en el kernel hasta que un fd esté listo.
5. En el servidor secuencial, si el primer cliente no mandaba nada el servidor quedaba bloqueado en su `recv()` y no aceptaba ni atendía a nadie más. `select()` resuelve eso porque pregunta por **todos** los sockets a la vez y solo llama a `recv()`/`accept()` sobre los que ya están listos, que no bloquean. Un solo hilo atiende a quien esté listo.

### Ejercicio 2

1. **1 thread** (medido con 3 clientes conectados).
2. Sí, responde enseguida. `select()` devuelve solo los sockets listos, y el del tercer cliente está listo aunque los otros dos no manden nada: nadie espera a nadie.
3. Imprime `- cliente (...) (total: N)`. Lo detecta `datos = sock.recv(4096)` devolviendo `b''` (rama `else` de `if datos:`).
4. Con `--bug` (sin `remove` pero con `close()`), el servidor **se cae** en el siguiente `select()` con `ValueError: file descriptor cannot be a negative integer (-1)`: en la lista quedó un socket cerrado, cuyo `fileno()` es -1.
5. El caso del "giro infinito" aparece si además no se cierra el socket (`--bug-sin-close`): **~90 % de CPU** y `select()` volvió más de 1,7 millones de veces en 2 s. Un fd en EOF está **siempre** "listo para leer" (`recv()` devuelve `b''` al instante), así que `select()` nunca bloquea.
6. Restaurado: el modo normal funciona bien.
7. Con 1100 sockets el último tiene fd 1102: `ValueError: filedescriptor out of range in select()`, vigilando **un solo** socket.
8. El límite es el **número** del fd (tiene que ser < `FD_SETSIZE` = 1024), no la cantidad: `fd_set` es un bitmap de 1024 bits indexado por número de fd.
9. Con `poll()` no falla: devolvió `[(1102, 16)]`. El 16 es `POLLHUP`, porque el socket no está conectado.
10. En desarrollo hay pocas conexiones y los fds son chicos. En producción, con muchas conexiones, archivos abiertos, logs, etc., los números pasan de 1023 y de golpe `select()` revienta, incluso en una llamada que vigila pocos sockets.

### Ejercicio 3 (obligatorio)

**A.** Tabla de mi máquina (`ej3_comparar.py`, µs por llamada, 3 sockets activos):

| conexiones | select | poll | epoll |
|---:|---:|---:|---:|
| 100 | 20,5 | 5,2 | 1,9 |
| 500 | 86,7 | 33,2 | 1,5 |
| 1000 | falla (ValueError) | 68,1 | 1,4 |
| 2000 | falla (ValueError) | 109,9 | 1,4 |
| 5000 | falla (ValueError) | 303,7 | 1,0 |

2. `poll()`: de 5,2 a 303,7 µs, un factor de **~58×** para 50× más conexiones. Crece lineal.
3. `epoll()`: de 1,9 a 1,0 µs, **plano** (el ruido de medición pesa más que la diferencia). No depende del total.
4. `select()` falla desde 1000 conexiones. Cada conexión es un `socketpair` (2 fds), así que con 1000 pares los fds pasan de 1023. Coincide con el 2.3: lo que importa es el número de fd, no la cantidad vigilada.

**B.**

5. En un servidor web la mayoría de las conexiones están ociosas: keep-alive esperando el próximo request, clientes leyendo la página, conexiones lentas de celulares. En cada instante solo unas pocas tienen datos.
6. `poll()` recibe **toda la lista** de fds en cada llamada, el kernel la copia y revisa uno por uno, y después Python recorre el resultado: es O(n) con n = vigilados. `epoll` registra los fds **una sola vez** (`epoll_ctl`), el kernel mantiene una lista de "listos" que se llena por callbacks cuando llega un paquete, y `epoll_wait` solo devuelve esa lista: O(listos).
7. Con `--activos 0.5` (la mitad con datos) la ventaja **desaparece**:

| conexiones | select | poll | epoll |
|---:|---:|---:|---:|
| 100 | 11,2 | 4,0 | 5,7 |
| 500 | 64,9 | 22,4 | 51,4 |
| 1000 | falla | 68,5 | 73,1 |
| 2000 | falla | 161,6 | 191,7 |
| 5000 | falla | 457,0 | 213,0 |

   Si la mitad está lista, O(listos) ≈ O(n): epoll también tiene que devolver y procesar n/2 eventos, y hasta resulta más lento que poll en 500-2000. En 5000 epoll "gana" porque `epoll.poll()` en Python devuelve como máximo 1023 eventos por llamada (`maxevents` por defecto), no porque haga menos trabajo.

**C.**

8. Con 10, 50 y 100 conexiones: select 2,1 / 7,0 / 13,2 µs, poll 0,7 / 1,6 / 3,0 µs, epoll 0,9 / 1,4 / 0,9 µs. Son microsegundos, irrelevantes al lado de cualquier I/O real. **No vale la pena** complicarse por epoll ahí.
9. No tiene sentido el multiplexing cuando hay pocas conexiones simultáneas (decenas) o cuando el trabajo por conexión es de CPU. Ahí un thread o proceso por cliente (o un pool) de la clase 14 es más simple y alcanza. El multiplexing paga cuando hay **muchas conexiones, mayormente ociosas** (I/O-bound, C10K).

**D. Conclusión.** En mi máquina, con 5000 conexiones de las que solo 3 tienen datos, `poll()` tarda unos 304 µs por llamada y crece lineal con el total (58× al pasar de 100 a 5000). `epoll` se queda en ~1 µs sin importar cuántas haya, y `select()` ni siquiera funciona pasando el fd 1023. nginx usa un event loop con epoll: unos pocos procesos, cada uno atendiendo miles de conexiones, pagando solo por las que tienen actividad, y cada conexión ociosa le cuesta unos pocos KB de estado. Un Apache clásico (prefork/worker) dedica un proceso o thread a cada cliente: con 10000 conexiones son 10000 stacks de memoria y un scheduler repartiendo CPU entre miles de hilos que en su mayoría están esperando. En la clase 16 medí unos 26 KB de RSS por thread solo de base, y en la clase 17 el servidor con selectors sostuvo 9500 conexiones con **un thread y 13 MB**. Por eso nginx atiende muchas más conexiones con la misma máquina.

### Ejercicio 4

1. Desaparecen la lista `vigilados` (el selector lleva el registro de qué se vigila), el `vigilados.remove()` (ahora es `sel.unregister()`) y el diccionario `direcciones`: la dirección va en `key.data` al registrar. Tampoco hace falta separar las tres listas de `select()`.
2. `DefaultSelector` en mi máquina: **`EpollSelector`**.
3. Con `SelectSelector` y pocos clientes el comportamiento es idéntico (probado). Pero hereda el límite de `select()`: con un fd > 1023 tira `ValueError: filedescriptor out of range in select()` (probado con fd 1103).
4. Sin `sel.unregister(conn)` antes del `close()`, el primer cliente anda, pero cuando llega **el siguiente** el kernel le asigna el mismo número de fd (el más bajo libre) y `sel.register()` falla con `KeyError: "... (FD 5) is already registered"`. El servidor se cae. El selector todavía tiene el fd viejo en su mapa interno: el estado quedó inconsistente.

### Ejercicio 5

1. `sendall()` reintenta hasta mandar todo. En un socket no bloqueante, si el buffer del kernel está lleno, lanza `BlockingIOError` a mitad de camino y no sabés cuánto se mandó. En uno bloqueante, frena al único hilo y con él a todos los clientes. `send()` manda lo que entre ahora y devuelve cuánto fue, y el resto queda en el buffer para cuando el selector avise. En la clase 13 (un hilo por conexión, bloqueante) recomendábamos `sendall()` porque bloquear ese hilo no afectaba a nadie más.
2. Con `EVENT_WRITE` permanente: **~85 % de CPU** con un cliente ocioso, y **2,4 millones de eventos** procesados en 3 s (contra 4 en el modo correcto, con 1 % de CPU). Un socket casi siempre tiene lugar en el buffer de envío, así que siempre está "listo para escribir" y `select()` nunca duerme.
3. Con `sendall()`, cuando el buffer del cliente lento se llena el hilo único se bloquea (o, no bloqueante, da error) y **los otros 999 clientes quedan congelados**. Con buffer + `EVENT_WRITE`, al lento simplemente se le acumulan bytes en su buffer de usuario y los demás siguen atendidos.
4. La memoria crece en el **buffer de salida del servidor** (`pendiente[conn]`) de ese cliente, que no tiene tope. Habría que poner un **límite por cliente**: dejar de leerle (backpressure) o desconectarlo si pasa de X bytes. Un timeout de escritura también ayuda.

### Ejercicio 6

1. Porque hay **un solo hilo**: mientras corre `difundir()` no hay otro código tocando `clientes` ni `salida`. No hay intercalado preventivo, cada callback corre entero antes del siguiente. Con threads, dos handlers podrían modificar el diccionario o escribir en el mismo socket al mismo tiempo.
2. Evita bloquear el loop con un cliente lento: si se escribiera directo y el buffer de un destinatario estuviera lleno, se trabaría todo el chat (o se perderían bytes con `send()` parcial). Encolar desacopla al que manda del que recibe.
3. `/nick <nombre>`: implementado. Valida que no esté en uso y avisa a los demás.
4. `/lista`: implementado. Responde `N conectados: ana, beto`.
5. No, no es cierto. TCP es un flujo de bytes: un `recv()` puede traer **media línea** (si `nc` manda sin `\n`, si el mensaje es largo o llega en dos segmentos) o **varias líneas juntas**. Con el chat original, mandando `hola me` y después `dia linea\nuno\ndos\n`, B recibió `<x> hola me`, y en otro mensaje `<x> dia linea\nuno\ndos`: una línea partida en dos y tres líneas pegadas en una.
6. Arreglado con `entrada[conn]`: se acumula y se corta por `\n`, procesando solo líneas completas. El resto queda en el buffer. Con la misma prueba B recibió `<ana> hola media linea`, `<ana> uno`, `<ana> dos`. También hay un tope (`MAX_LINEA`) para el que nunca manda `\n`.

### Ejercicio 7

1. **No responde.** En modo event loop puro, el `ping` del segundo cliente (mandado a los 0,3 s) se respondió recién a los **3,27 s**, junto con el cálculo del primero.
2. Con un thread por cliente (como `server_threads.py`) **no pasa**: el `ping` respondió a los **0,33 s** y el cálculo a los 2,85 s. El GIL igual reparte el intérprete entre threads cada pocos ms, así que el thread del ping avanza.
3. Regla: **nunca bloquear el event loop**. Todo callback tiene que ser corto y no bloqueante: nada de CPU pesada ni de I/O bloqueante adentro del loop.
4. Mandar el trabajo pesado **afuera del loop**: un pool de procesos (`ProcessPoolExecutor`), y que el resultado vuelva al loop como un evento más. Implementado en `--pool`, que avisa por un `socketpair` (self-pipe). Resultado: `ping` a los 0,31 s y cálculo a los 2,78 s, con el loop siempre libre. Es lo mismo que `loop.run_in_executor()` en asyncio, y el modelo del TP2.

### Adicionales

- **Servidor con timeout**: `select(timeout=...)` despierta aunque no haya eventos y en cada vuelta se cierran los inactivos. Probado con 1,5 s: el cliente recibe "Desconectado por inactividad".
- **Proxy TCP**: dos sockets por túnel, con un diccionario `par` y un buffer de salida por socket. El EOF se propaga con `shutdown(SHUT_WR)` recién cuando se vació el buffer, para no perder datos en vuelo, y se ignoran eventos de sockets que se cerraron en la misma tanda. Probado con 3 transferencias simultáneas de 5 MB: ida y vuelta idénticas.
- **Medir el techo**: `servidor_selectors.py` sostuvo **9500 conexiones con 1 thread, 9505 fds y 13 MB de RSS** (en la clase 16, 1000 conexiones con threads eran 1001 threads y 39 MB). El límite real lo pone `ulimit -n`, que acá es 20000. Con `ulimit -n 1024` en el servidor, a las ~1020 conexiones `accept()` tira `OSError: [Errno 24] Too many open files` y, como el servidor de la cátedra no lo maneja, **se cae**. Un servidor serio tiene que atrapar `EMFILE` y seguir. Con threads, el techo además depende de la memoria por thread (8 MB de stack virtual cada uno) y del scheduler.
- **Self-pipe**: el handler de SIGINT/SIGTERM solo escribe un byte en un pipe no bloqueante registrado en el selector. Ctrl+C llega como evento del loop, y el cierre (avisar a los clientes, unregister, close) se hace en un punto seguro, fuera del handler. Probado con `kill -INT`: el cliente recibe "El servidor se apaga. Chau." y el proceso sale con código 0.
