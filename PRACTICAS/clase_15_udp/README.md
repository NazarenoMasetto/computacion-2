# Clase 15 - UDP

Todos los scripts aceptan `--port N`. Puertos por defecto los de la consigna (8080, 8081 para el truncado,
8082 para broadcast); los adicionales usan 8037 (tiempo), 8083 (MTU), 8084 (multicast), 8085 (medidor).
`comandos.sh` tiene netcat UDP, MTU y los comandos de `tc netem` (necesitan sudo y se deshacen solos al final).

## Ejercicios → archivos → cómo correrlos

| Ejercicio | Archivo(s) | Terminal 1 | Terminal 2 |
|---|---|---|---|
| 1.1 Servidor y cliente | `ej1_echo_udp.py` | `python3 ej1_echo_udp.py servidor` | `python3 ej1_echo_udp.py cliente --mensaje "hola profe"` (punto 4: `--sin-timeout`) |
| 1.2 Contra netcat | `ej1_echo_udp.py`, `comandos.sh` | `nc -u -l 8080` (`bash comandos.sh nc_servidor`) | `python3 ej1_echo_udp.py cliente` |
| 1.3 Dos clientes | `ej1_echo_udp.py` | `python3 ej1_echo_udp.py servidor` | dos `python3 ej1_echo_udp.py cliente` a la vez |
| 2.1 Límites | `ej1_echo_udp.py` | `python3 ej1_echo_udp.py servidor` | `python3 ej1_echo_udp.py tres` |
| 2.2 Truncado | `ej2_truncado.py` | — | `python3 ej2_truncado.py` |
| 3 A Pérdidas | `ej3_perdidas.py`, `comandos.sh` | — | `python3 ej3_perdidas.py 0.3`; con tc real: `bash comandos.sh perdida_real` |
| 3 B Reintentos | `ej3_confiable.py` | `python3 ej3_confiable.py servidor --protocolo simple --perdida 0.3` | `python3 ej3_confiable.py cliente --protocolo simple --perdida 0.3` (y `--perdida 0.7 --intentos 50`, `--timeout 0.01`, `--timeout 5`) |
| 3 C Duplicados | `ej3_confiable.py` | idem `--protocolo simple` | idem: comparar "envíos reales" con "veces que el servidor hizo el trabajo" |
| 3 D Secuencia | `ej3_confiable.py` | `python3 ej3_confiable.py servidor --protocolo seq --perdida 0.3` | `python3 ej3_confiable.py cliente --protocolo seq --perdida 0.3` |
| 3 D.11 Respuestas viejas | `ej3_confiable.py` | `... servidor --protocolo simple --perdida 0 --demora 0.05` (y `seq`) | `... cliente --protocolo simple --perdida 0 --timeout 0.01 --n 10 --intentos 20` (y `seq`) |
| 4 connect() en UDP | `ej4_connect_udp.py` | — | `python3 ej4_connect_udp.py` (prueba las 3 variantes) |
| 5 Broadcast | `ej5_broadcast.py` | `python3 ej5_broadcast.py servidor` | `python3 ej5_broadcast.py cliente` (punto 1: `--sin-permiso`) |
| 6 MTU / fragmentación | `ej6_mtu.py`, `comandos.sh` | — | `python3 ej6_mtu.py --perdida 0` (punto 3), `python3 ej6_mtu.py --perdida 0.05 --veces 1000` (simulado); con tc real: `bash comandos.sh fragmentacion_real` |
| Adic. tiempo RFC 868 | `ad_tiempo.py` | `python3 ad_tiempo.py servidor --atraso 5` | `python3 ad_tiempo.py cliente` |
| Adic. chat multicast | `ad_chat_multicast.py` | `python3 ad_chat_multicast.py --nombre ana` | `python3 ad_chat_multicast.py --nombre beto` (y escribir) |
| Adic. pérdida y jitter | `ad_medidor.py` | `python3 ad_medidor.py receptor` | `python3 ad_medidor.py emisor --n 1000` (y `--perdida 0.1 --desorden 0.05`) |
| Adic. traceroute | `ad_traceroute.py` | — | `sudo python3 ad_traceroute.py 8.8.8.8` |

## Qué se probó (Linux, Python 3.13, puertos 28200-28299)

Todo lo de la tabla, salvo lo que necesita **`tc`** (`perdida_real` y `fragmentacion_real`): en la
máquina de prueba no estaban `tc` ni `ip` (tampoco `ss`). Para no quedarme sin la parte 6, `ej6_mtu.py`
simula la pérdida **por fragmento** y compara con la cuenta teórica. Broadcast y traceroute se probaron
solo en una máquina (sin un compañero en la red). Los números dependen de la máquina y del azar.

## Respuestas

### Ejercicio 1
1. `recvfrom()` devuelve los datos **y** la dirección del remitente `(ip, puerto)`; es lo que se usa para contestarle con `sendto()`.
2. Sí, cambia cada vez (57605, 45122, 43182): cada corrida crea un socket nuevo y el kernel le asigna un puerto efímero libre al primer `sendto()`.
3. El cliente manda "al vacío" y espera: `Sin respuesta en 2s`. Tarda lo que dure el timeout (2,05 s medidos); UDP no tiene conexión que se rompa.
4. Sin `settimeout` espera para siempre (lo cortó el `timeout 3` de la prueba). Un `recvfrom` sin timeout en UDP es un cuelgue esperando a pasar.
5. Sí, el `nc -u -l` recibe `hola mundo`.
6. Sí: lo que escribí en el `nc` le llegó al cliente (`eco de ('127.0.0.1', 8080): b'respuesta de nc\n'`). `nc -u -l` contesta al último remitente.
7. Desaparecen `listen()`, `accept()` y `connect()`; y `recv`/`send` pasan a ser `recvfrom`/`sendto`.
8. En TCP cada conexión es una cuádrupla distinta y tiene su propio socket (estado: secuencias, ventanas, buffers). UDP no tiene estado de conexión: cada datagrama trae su origen, así que un solo socket ligado a (IP, puerto) recibe de todos y responde a cada `origen`.
9. Sí, atendió a los dos (los datagramas `A` y `B` se intercalaron) sin threads ni procesos. Como no hay sesión, cada pedido es un datagrama independiente que se procesa y responde al toque; nadie "ocupa" el servidor. (Si el procesamiento fuera lento, igual habría que pensar en concurrencia.)

### Ejercicio 2
1. Tres `sendto()` → tres `recvfrom()`:
   ```
   [4] recvfrom 4 bytes de 127.0.0.1:56266: b'HOLA'
   [5] recvfrom 4 bytes de 127.0.0.1:56266: b'COMO'
   [6] recvfrom 5 bytes de 127.0.0.1:56266: b'ESTAS'
   ```
2. En TCP llegaron fusionados (`HOLACOMOESTAS` en un `recv`). UDP es orientado a **mensajes**: cada datagrama es una unidad indivisible; TCP es un flujo de bytes sin límites.
3. Primero 10 bytes; el segundo: nada (timeout).
4. Se descartaron: el kernel entrega un datagrama por `recvfrom` y lo que no entra en el buffer se tira. Con `recvmsg` se ve el aviso: `MSG_TRUNC=True`.
5. En TCP quedarían en el buffer para el próximo `recv()`, porque es un flujo continuo. En UDP la unidad es el datagrama: o lo leés entero o perdés el resto.
6. 65535 (el máximo de un datagrama UDP/IPv4; payload real 65507), así nunca truncás. O el máximo que tu protocolo define, si lo controlás.

### Ejercicio 3 (obligatorio)
**Parte A**
1. Con 0,3: llegaron 138 de 200 (perdidos 62, 31%).
2. Ninguno: "Errores vistos por el emisor: 0". `sendto()` devolvió éxito siempre.
3. UDP no garantiza la entrega ni avisa cuando un datagrama se pierde: el emisor no se entera.
3b. No lo pude correr (no hay `tc` en la máquina de prueba). Lo esperable: saltos hacia atrás > 0 (con `reorder 25%`, varias decenas de 200). Un protocolo que asuma orden se rompe: procesa un mensaje viejo como si fuera el último, o lo descarta como duplicado. Hay que numerar.

**Parte B** (`pedir_con_reintentos` en `ej3_confiable.py`, pérdida simulada en los dos sentidos)
4. Con 30% por sentido: ~2,0-2,1 envíos por mensaje (en 300 mensajes: 2,11 / 2,07 / 2,08). Cuadra con la teoría: cada intento sale bien con prob. 0,7 × 0,7 = 0,49 → 1/0,49 ≈ 2,04. Con 5 intentos queda ~3-5% sin respuesta (0,51⁵ ≈ 3,5%).
5. Con 0,7 sí funciona pero hay que permitir muchos intentos: éxito por intento 0,3 × 0,3 = 0,09 → ~11 en promedio. Medí 9,0 y 8,3 envíos por mensaje (15 mensajes, `--intentos 50`). Con solo 5 intentos fallan la mayoría.
6. Timeout muy corto (0,01 s con un servidor que tarda 0,05 s): reintenta antes de que la respuesta pueda llegar, inunda al servidor con duplicados (50 trabajos para 10 mensajes) y en el modo simple recibe respuestas de pedidos anteriores (9 de 10 respuestas **incorrectas**). Muy largo (5 s): funciona pero cada pérdida cuesta 5 s; 5 mensajes con 30% de pérdida tardaron 55 s.

**Parte C**
7. No puede saberlo: en los dos casos lo único que ve es silencio hasta el timeout.
8. `--protocolo simple` cuenta el trabajo: 30 mensajes → 39 trabajos (30%); 15 mensajes con 70% → **45** trabajos. El servidor procesa de más.
9. "Pasar a mayúsculas" es **idempotente**: hacerlo dos veces da lo mismo. "Transferir $100" no: cada duplicado es otra transferencia y te sacan $100 de más.

**Parte D** (`--protocolo seq`)
10. El servidor guarda `(origen, seq) → respuesta`; si llega un duplicado reenvía la guardada sin rehacer el trabajo. Medido: 30 mensajes → 30 trabajos (con 50 envíos reales); 15 mensajes al 70% → 15 trabajos con 124 envíos. Coincide.
11. Porque una respuesta demorada de un intento anterior puede llegar mientras espero la del pedido actual y la tomaría como propia. Con `--timeout 0.01` y el servidor demorado: modo simple = 9 respuestas incorrectas; modo seq = 0 incorrectas y 37 respuestas viejas descartadas.
12. `confiable.py 0.6` (cátedra): 5 mensajes, **13 envíos reales**, **5** trabajos del servidor. Igual que el mío: los reintentos no se convierten en trabajo repetido.

**Parte E**
13. Le faltan, por ejemplo: control de flujo (no saturar al receptor) y de congestión (no saturar la red); entrega ordenada de un flujo con ventana (acá es stop-and-wait: un mensaje a la vez, lentísimo); establecimiento/cierre de conexión (saber que el otro está y que terminó); checksum fuerte/segmentación de mensajes grandes, y limpieza del diccionario `vistos` (hoy crece para siempre).
14. Cuando necesitás todo eso: entrega confiable y ordenada de muchos datos. Reimplementar ventana, congestión y retransmisión adaptativa es reescribir TCP (peor). UDP conviene cuando podés tolerar pérdidas o la info vieja ya no sirve (voz, video, juegos, DNS de un pedido-respuesta) o necesitás broadcast/multicast; o si usás algo ya hecho como QUIC.

### Ejercicio 4
1. `ConnectionRefusedError`. Sale del **ICMP port unreachable** que manda el kernel destino; como el socket está "conectado", el kernel sabe a qué socket asociar ese error y te lo entrega en la siguiente operación.
2. Sin `connect()`: timeout (2 s). El ICMP llega igual pero el kernel no lo asocia a un socket no conectado (en Linux el error se ignora).
3. `connect()` en UDP no manda nada por la red: solo fija la dirección por defecto (permite `send`/`recv`), **filtra** lo que se recibe a esa dirección y habilita que se reporten los errores ICMP asociados.
4. Probado con dos puertos locales: conectado a A, recibí solo `b'soy A (el conectado)'`; el datagrama de B lo descartó el kernel.
5. Porque el ICMP puede no llegar nunca (firewalls que lo bloquean, NAT, pérdida) o llegar tarde; no es confiable como detector. Además un ICMP se puede falsificar. En Internet hay que basarse en timeouts y en el propio protocolo.

### Ejercicio 5
1. `PermissionError: [Errno 13] Permission denied`. Es una protección para que un programa no mande broadcast "sin querer" (por ej. una IP mal configurada) e inunde a toda la red: hay que pedirlo explícitamente con `SO_BROADCAST`.
2. `ej5_broadcast.py servidor` responde `AQUI <hostname>`. En la prueba: `('192.0.2.2', 28221) respondió: b'AQUI vm'`.
3. Solo lo pude probar en una máquina (funciona). En la misma red debería contestar cada compañero que tenga el servidor corriendo (el cliente junta todas las respuestas). En redes distintas no: el broadcast no pasa el router.
4. Porque un broadcast inundaría Internet entera (y con bucles se multiplicaría): el broadcast queda limitado al dominio de broadcast (la LAN). Por diseño y seguridad (amplificación tipo "smurf").
5. TCP necesita conocer la IP del otro para hacer el handshake (y tener una IP propia). Una máquina sin IP no sabe a quién conectarse ni tiene dirección para recibir el SYN-ACK; con broadcast UDP manda a "todos" desde 0.0.0.0 y el servidor DHCP le contesta.

### Ejercicio 6
1. En la máquina de prueba: `lo` 65536, `eth0` 1400, `docker0` 1500.
2. Con MTU 1500: 1500 − 20 (IP) − 8 (UDP) = **1472 bytes** (con la `eth0` de 1400 serían 1372).
3. Sí, llega (20/20). Ojo: por `lo` (MTU 65536) ni siquiera se fragmenta. Por Ethernet (1500) son **41 fragmentos**.
4. y 5. Sin `tc`, simulado con 5% de pérdida **por fragmento** (`ej6_mtu.py --perdida 0.05 --veces 1000`):

| Tamaño | Fragmentos | Llegaron | Teórico (0,95^k) |
|---|---|---|---|
| 60000 B | 41 | 128/1000 (13%) | 12% |
| 1000 B | 1 | 952/1000 (95%) | 95% |

Con 20 envíos dio 3/20 vs 19/20. La diferencia es mucho mayor que 5% porque el datagrama llega solo si llegan **todos** sus fragmentos (IP no retransmite fragmentos sueltos): P = 0,95^41 ≈ 0,12. O sea, pierdo el 88% de los datagramas grandes con solo 5% de pérdida por paquete. Y encima, si TCP/la app retransmite, reenvía los 41 fragmentos otra vez. Por eso conviene mandar datagramas ≤ MTU − 28.

### Adicionales
- **Tiempo RFC 868**: 4 bytes `!I` con segundos desde **1900** (se suma 2208988800 a epoch Unix, como dice la RFC). Con `--atraso 5` el cliente midió `desfasaje +4.7 s` (resolución de 1 s, RTT 0,55 ms; usa el punto medio del RTT como hora local).
- **Chat multicast**: grupo 239.1.2.3, TTL 1. Probado con dos instancias en la misma máquina: ambos vieron los mensajes. Con multicast el emisor hace **un** `sendto` y la red lo replica solo donde hay miembros; con TCP serían N conexiones y N envíos del mismo mensaje (tráfico y CPU del emisor × N).
- **Medidor**: 1000 datagramas cada 1 ms en loopback → 0 perdidos, 0 desordenados, entre llegadas media 1,26 ms y jitter (desvío) 0,27 ms (RFC 3550: 0,25 ms). Con red simulada (10% pérdida, 5% desorden): 42/500 perdidos (8,4%) y 21 desordenados.
- **Traceroute**: UDP con `IP_TTL` creciente + socket raw ICMP (tipo 11 = time exceeded, 3/3 = port unreachable = llegué). Corrido como root: hacia 8.8.8.8 mostró 2 saltos y después `*` (la salida a Internet del sandbox está filtrada); a una IP local responde en el salto 1.
