# Clase 13 - Sockets TCP

Todos los scripts usan el puerto **8080** por defecto y aceptan `--port N`.
Python 3.10+, solo stdlib. `comandos.sh` tiene los comandos de terminal (nc, ss) comentados;
si `ss` no está instalado, la función `conexiones` lee `/proc/net/tcp`.

## Ejercicios → archivos → cómo correrlos

| Ejercicio | Archivo(s) | Terminal 1 | Terminal 2 |
|---|---|---|---|
| 1.1 Cliente vs nc | `ej1_cliente_nc.py` | `nc -l 8080` | `python3 ej1_cliente_nc.py` (punto 3: `--sin-recv`) |
| 1.2 Servidor vs nc | `ej1_servidor_nc.py` | `python3 ej1_servidor_nc.py` (punto 5: `--loop`) | `nc localhost 8080` |
| 1.3 SO_REUSEADDR | `ej1_servidor_nc.py`, `comandos.sh` | `python3 ej1_servidor_nc.py --sin-reuse` → Ctrl+C → relanzar | `nc localhost 8080`; `bash comandos.sh ej1_3` |
| 2.1 Lecturas parciales | `servidor_eco.py`, `ej2_lecturas_parciales.py` | `python3 servidor_eco.py` | `python3 ej2_lecturas_parciales.py --tope 4` (y `--tope 1`, `--tope 65536`) |
| 2.2 Señal de cierre | `ej2_cierre.py` | `python3 servidor_eco.py` (luego Ctrl+C) | `python3 ej2_cierre.py --sin-chequeo` / `python3 ej2_cierre.py` |
| 2.3 send vs sendall | `ej2_send_vs_sendall.py` | (trae su propio receptor) | `python3 ej2_send_vs_sendall.py` y `... --timeout 2` |
| 3 A. El problema | `ej3_tres_envios.py` | `python3 servidor_eco.py` | `python3 ej3_tres_envios.py` |
| 3 B. Delimitador | `ej3_framing_lineas.py` | `python3 ej3_framing_lineas.py servidor` | `nc localhost 8080` / `python3 ej3_framing_lineas.py cliente --modo juntos\|bytes\|newline` |
| 3 C. Longitud | `ej3_framing_longitud.py` | `python3 ej3_framing_longitud.py servidor` | `python3 ej3_framing_longitud.py cliente --modo juntos\|bytes\|newline\|vacio` |
| 4 Bytes/encoding | `ej4_encoding.py` | — | `python3 ej4_encoding.py` |
| 5.1 Reintentos | `ej5_reintentos.py` | (unos segundos después) `python3 servidor_eco.py` | `python3 ej5_reintentos.py` (primero) |
| 5.1/5.2 Rechazo y timeout | `ej5_timeout.py` | `python3 servidor_eco.py` (o nada, para el rechazo) | `python3 ej5_timeout.py --timeout 3` / `--timeout 0` |
| 5.3 Servidor robusto | `servidor_eco.py`, `comandos.sh` | `python3 servidor_eco.py` | `nc localhost 8080` y Ctrl+C |
| 6 Límite secuencial | `servidor_eco.py`, `comandos.sh` | `python3 servidor_eco.py --lento 10` (punto 5: `--backlog 1`) | varias `nc localhost 8080`; `bash comandos.sh ej6` |
| Adic. comandos | `ad_servidor_comandos.py` | `python3 ad_servidor_comandos.py` | `nc localhost 8080` → `TIME`, `ECHO hola`, `QUIT` |
| Adic. archivos | `ad_transferencia.py` | `python3 ad_transferencia.py servidor --destino recibidos` | `python3 ad_transferencia.py cliente archivo.bin`; `md5sum archivo.bin recibidos/archivo.bin` |
| Adic. HTTP mínimo | `ad_http_minimo.py` | (opcional) `python3 -m http.server 8080` | `python3 ad_http_minimo.py example.com` o `... localhost --port 8080` |
| Adic. getaddrinfo | `ad_getaddrinfo.py` | `python3 servidor_eco.py` | `python3 ad_getaddrinfo.py localhost` |

`ad_servidor_comandos.py` y `ad_transferencia.py` importan las funciones de framing de `ej3_*.py`
(correrlos desde esta carpeta).

## Qué se probó (Linux, Python 3.13, puertos 28000-28999)

- Todo lo de la tabla, con `nc` (OpenBSD) y con los clientes propios. Framing: los 3 casos (todo junto,
  byte por byte con sleep, `\n` adentro) y mensaje vacío → OK en ambas estrategias.
- Transferencia de un archivo aleatorio de 120 MB: md5 local = md5 remoto.
- HTTP mínimo contra `python3 -m http.server` local (OK, Content-Length coincide). Contra `example.com`
  el sandbox donde lo probé no tiene salida directa a Internet (un proxy devolvió 403), pero el parseo funcionó igual.
- Ej 6 con `--lento 3/8`: latencias escalonadas y estados de conexión leídos de `/proc/net/tcp`
  (la máquina no tenía `ss`; `comandos.sh` usa `ss` si existe).

## Respuestas

### Ejercicio 1
1. Sí, en el `nc` aparece `hola desde Python`.
2. Lo que escribís en el `nc` le llega al cliente: `Recibido: b'respuesta de nc\n'`. El cliente estaba bloqueado en `recv()` hasta eso.
3. Sin el `recv()` el cliente manda y cierra enseguida; el `nc` ve el mensaje y después el EOF (termina). El servidor no "nota" que no leímos: TCP no avisa si la aplicación leyó o no.
4. `dir` es `('127.0.0.1', 37354)`: IP y puerto **efímero** del cliente. Junto con IP:puerto del servidor forman la cuádrupla que identifica la conexión.
5. Meter el `accept()` en un `while True` (eso hace `--loop`), y cerrar cada `conn` al terminar.
6. `OSError: [Errno 98] Address already in use`.
7. Sí: queda el puerto del servidor en `TIME-WAIT` (lo vi en `/proc/net/tcp` con estado `06`: `0100007F:6D77 ... 06`). Lo deja el que cierra primero, en este caso el servidor al matarlo.
8. Sí, desaparece. Detalle que encontré probando: en Linux **las dos** ejecuciones tienen que haber usado `SO_REUSEADDR`. Si el server viejo no la tenía, el nuevo con reuse igual falla mientras dure el TIME_WAIT.

### Ejercicio 2
1. Con `recv(4)` se ejecutó 12 veces (47 bytes) y no se perdió ningún byte.
2. `recv(1)`: 47 llamadas, todo llega igual (más lento). `recv(65536)`: 1 sola llamada en loopback.
3. Porque el tope es un **máximo**: `recv` devuelve lo que ya está en el buffer del kernel. Si el resto todavía viene viajando (segmentos, MSS, ventana), devuelve lo parcial.
4. Al matar el servidor, `recv()` devuelve `b''` sin bloquear, una y otra vez: el bucle imprime `recv devolvió: b''` a lo loco (en 0,7 s imprimió ~150.000 líneas).
5. `if not datos: break` (b'' significa EOF: el otro lado cerró).
6. Porque una vez cerrado, `recv()` ya no se bloquea nunca: vuelve al instante con `b''`, así que el bucle gira sin dormir nunca → 100% de un núcleo.
7. `send()` devuelve la cantidad de bytes que el kernel aceptó (puede ser menos). `sendall()` repite hasta mandar todo y devuelve `None` (o lanza excepción).
8. Con socket bloqueante en loopback, `send()` de 10 MB devolvió 10485760 (Linux bloquea hasta mandar todo). Con `settimeout(2)` (el socket queda no bloqueante por dentro) devolvió **3919467**: no mandó todo. Por eso no hay que confiar en `send()`.
9. Cuando no querés bloquearte: sockets no bloqueantes / `select`, donde mandás lo que entre, guardás el resto y seguís atendiendo otras cosas. También para controlar progreso o ritmo de envío.

### Ejercicio 3
1. Un solo `recv()`: `[127.0.0.1:49216] recv 13 bytes: b'HOLACOMOESTAS'`.
2. No. TCP es un **flujo de bytes**: garantiza orden e integridad, no límites de mensaje. Fusionar los tres envíos es legal.
3. Con `nc`: cada línea vuelve en mayúsculas (`HOLA NC`, `CHAU`).
4. Sí, tres respuestas: `[b'UNO', b'DOS', b'TRES']`.
5. Sí, funciona igual: `[b'HOLA']`. El buffer junta los pedazos hasta ver el `\n`.
6. Porque `recv(n)` puede devolver menos de `n`. Si leés la cabecera de 4 bytes y solo llegan 2, el protocolo se desincroniza para siempre.
7. Con longitud funciona (`[b'LINEA CON\nSALTO ADENTRO']`). Con delimitador el mensaje se parte en dos (`[b'LINEA CON', b'SALTO ADENTRO']`): habría que escapar el `\n`.
8. 0 bytes: llega cabecera `00000000` y un mensaje vacío válido (lo probé: `[b'', b'DESPUES DEL VACIO']`); hay que distinguir `b''` (vacío) de `None` (cierre). 5 GB: no entra en `'!I'` (máx 4 GiB-1) → `struct.error`; habría que usar `'!Q'` y además no cargarlo entero en memoria sino mandarlo por bloques (como en `ad_transferencia.py`). Del lado receptor conviene poner un tope máximo para que nadie te haga reservar 4 GB.
9. Tabla:

| | Delimitador | Longitud |
|---|---|---|
| Contenido binario arbitrario | No (sin escapar el delimitador) | Sí |
| Depurable con `nc` | Sí, es texto | Difícil (cabecera binaria) |
| Hay que saber el tamaño antes | No | Sí |

10. Los headers son texto chico y variable que se lee línea a línea (cómodo de depurar y de generar sin saber el tamaño); el cuerpo puede ser binario y grande, así que conviene saber cuántos bytes leer exactos (y no tener que escanear buscando un delimitador).

### Ejercicio 4
1. `TypeError: a bytes-like object is required, not 'str'`: los sockets mandan bytes; hay que `.encode()`.
2. `'ñ'` → `b'\xc3\xb1'`; `len('año')=3` y `len(bytes)=4` porque en UTF-8 la ñ ocupa 2 bytes.
3. `UnicodeDecodeError: ... unexpected end of data`: se cortó la ñ a la mitad.
4. Decodificando **mensajes completos** (framing del ej. 3) o con un decodificador incremental (`codecs.getincrementaldecoder`), que guarda el byte suelto hasta que llega el resto.
5. Para mostrar/loguear texto donde un carácter roto no importa (logs, debug, datos de un tercero). Nunca cuando los datos se procesan o se guardan, porque perdés información sin enterarte.

### Ejercicio 5
1. `ConnectionRefusedError: [Errno 111] Connection refused` (el kernel contesta RST: no hay nadie en el puerto).
2. y 3. `ej5_reintentos.py`: lo lancé 2 s antes que el servidor → `Intento 1/2/3: rechazado...`, `Conectado en el intento 4`.
4. Se queda bloqueado en `recv()` para siempre (el eco no manda nada si no le mandás).
5. `TimeoutError: timed out` (antes `socket.timeout`, hoy es alias).
6. Porque un servidor colgado o una red cortada sin FIN te dejan el proceso/hilo trabado indefinidamente, acumulando recursos, sin forma de reaccionar.
7. Sí, sobrevive (probado matando `nc` con `kill -9`; la siguiente conexión se atendió bien).
8. `ConnectionResetError` y `BrokenPipeError`: son las que aparecen cuando el cliente desaparece de golpe (RST al leer, o escribir sobre una conexión cerrada). Se capturan esas y no `Exception` para no esconder bugs del propio servidor.

### Ejercicio 6 (medido con `--lento 3`, 4 clientes con 0,2 s de diferencia; depende de la máquina)
1. No responde: queda esperando, aunque `nc` se conectó.
2. Lo que tarde el primero más su propio trabajo: medí 3,0 / 5,8 / 8,6 / 11,4 s (escalones de `--lento`). Con `--lento 10` el segundo tarda ~20 s.
3. `ESTAB` lo completó el **kernel**: el handshake de 3 vías lo hace el sistema operativo y deja la conexión lista en la cola de aceptación; `accept()` solo la saca de la cola.
4. En `LISTEN`, `Recv-Q` = conexiones ya establecidas esperando `accept()` (la cola). Con un tercer cliente sube en 1.
5. Con `listen(1)` Linux admite backlog+1 = 2 en cola (vi `rx=2` en la línea LISTEN). Del cuarto en adelante los clientes quedan en `SYN_SENT` (estado `02`): el kernel descarta el SYN y el cliente lo **reintenta** (1 s, 3 s, 7 s...), así que no ve un rechazo, ve una demora; si la espera es muy larga termina en timeout.
6. Porque "conectó" solo significa que el kernel completó el handshake y lo encoló; la aplicación todavía no hizo `accept()` ni lee nada.
7. Un hilo por cliente (`threading`), un proceso por cliente (`fork`/`multiprocessing`) o un pool de workers (`ThreadPoolExecutor`/`Pool`). (Y la cuarta, I/O multiplexada con `select`/asyncio, que viene más adelante.)

### Adicionales
- **Comandos**: `TIME`, `ECHO <txt>`, `QUIT` con códigos tipo SMTP (220/200/221/500); lo de después de QUIT no se procesa.
- **Archivos**: 120 MB llegaron íntegros (md5 idéntico) en ~0,6 s por loopback.
- **HTTP**: arma `GET` con `Host` y `Connection: close`, separa headers del cuerpo por `\r\n\r\n` y compara `Content-Length` con lo recibido.
- **getaddrinfo**: recorre todas las direcciones (IPv6/IPv4) y se queda con la primera que conecta; en mi máquina `localhost` resolvía solo a IPv4.
