# Clase 12 - Redes: fundamentos

Python 3.13, stdlib. Puerto por defecto 8080 (el de la consigna). Todos los scripts aceptan otro puerto por argumento.

**Limitaciones del entorno de prueba.** En el contenedor donde se probó no estaban `ip`, `ss`, `dig`, `tcpdump` ni `traceroute`, y no había IPv6 ni salida libre a internet: un proxy intercepta el puerto 80 y responde `403 host_not_allowed`. Sí estaba `nc` (OpenBSD). Los comandos de esas herramientas están en `comandos.sh`. En las respuestas indico qué es esperado (E) y qué está probado de verdad (P).

| Ejercicio | Archivo(s) | Comando |
|---|---|---|
| 1, 2, 7 (lectura) y 3, 4, 5 comentados | `comandos.sh` | `./comandos.sh` (los interactivos se copian a mano) |
| 3 netcat | `comandos.sh` | Terminal 1: `nc -l 8080` / Terminal 2: `nc localhost 8080` |
| 4 HTTP a mano | `comandos.sh` | `printf 'GET / HTTP/1.1\r\nHost: example.com\r\nConnection: close\r\n\r\n' \| nc example.com 80` |
| 5 handshake | `comandos.sh` | `sudo tcpdump -i lo -n port 8080` + `nc -l 8080` + `echo test \| nc -N localhost 8080` |
| 6A/B TCP es un flujo (obligatorio) | `ej6_cliente_tcp.py`, `ej6_servidor_tcp.py` | `nc -l 8080 \| od -c` (o `python3 ej6_servidor_tcp.py`) y `python3 ej6_cliente_tcp.py [--pausa 1]` |
| 6C UDP | `udp_srv.py`, `ej6_cliente_udp.py` | `python3 udp_srv.py` y `python3 ej6_cliente_udp.py` |
| 7 Puertos efímeros | `ej7_puertos_efimeros.py` | `python3 ej7_puertos_efimeros.py [--familia 4\|6] [--host H --puerto P]` |
| Adicional: escaneo propio | `ej_adicional_escaneo.sh` | `./ej_adicional_escaneo.sh 1 1024` (solo 127.0.0.1) |
| Adicional: transferir archivo | `ej_adicional_transferencia.sh` | `./ej_adicional_transferencia.sh archivo [puerto]` |
| Adicional: costo del handshake | `ej_adicional_handshake.py` | `python3 ej_adicional_handshake.py --remoto example.com:80` |

## Qué se probó (P)

- **Ej. 6 con `nc -l | od -c`**: llega `H O L A C O M O E S T A S` todo seguido, tanto sin pausa como con pausa (`od` junta todo y no muestra los límites).
- **Ej. 6 con `ej6_servidor_tcp.py`**: muestra cada `recv()`. Sin pausa: `recv #1: b'HOLACOMOESTAS'`, o sea 1 recv para 3 send. Con `--pausa 1`: 3 recv separados.
- **Ej. 6C**: 3 `recvfrom`, uno por datagrama.
- **Ej. 7**: rango `32768 60999`. Puertos asignados: 42568, 42578, 42582, 42592, 42600 (dentro del rango, crecientes y pares). Tupla de 2 elementos (IPv4). Forzar `--familia 6` falla con un mensaje claro porque no hay IPv6.
- **Ej. 3.2**: con `strace` vi que el `nc` de Debian/Ubuntu activa `SO_REUSEPORT`, así que el segundo `nc -l 8080` **no** da error. Con Python (`bind` sin reuseport) sí aparece `OSError: [Errno 98] Address already in use`.
- **Adicionales**: el escaneo encontró el puerto abierto de prueba. La transferencia con `nc` dio el mismo md5. El handshake local tardó ~0.1 ms (la medición "remota" no es real acá, porque el proxy contesta localmente).

## Respuestas

### Ej. 1 (E)
1. Normalmente hay `lo` (loopback, `127.0.0.1`) más una placa real (`eth0`, `enp…` o `wlan0`) y quizá `docker0`. En el contenedor: `lo`, `eth0`, `docker0`, `ifb0`, `ifb1` (visto en `/sys/class/net`).
2. La IP de la LAN suele ser privada (`192.168.x.x` o `10.x.x.x`): no sale a internet tal cual, el router hace NAT.
3. Si hay IPv6, aparece al menos una `fe80::…/64`, que es link-local: solo sirve dentro del enlace físico.
4. El gateway es la línea `default via 192.168.1.1 dev wlan0`.
5. Está en la misma subred que mi IP (mismo prefijo, ej. `/24`). Tiene que ser así para alcanzarlo directo. Todo lo que no es de la red local se le manda a él.
6. Ejemplos típicos: `sshd` en 22, `cupsd` en 631, `systemd-resolved` en 53 y algún servidor de desarrollo en 8000/5432.
7. Lo que escucha en `127.0.0.1` solo se ve desde la propia máquina. Lo que escucha en `0.0.0.0` o `*` lo puede alcanzar cualquiera de la misma wifi (si el firewall lo deja).

### Ej. 2 (E)
1. La IP aparece en la `ANSWER SECTION` (registro `A`, a veces precedido por un `CNAME`).
2. El TTL son los segundos que esa respuesta puede quedar en cache antes de volver a preguntar.
3. Sí, baja, porque la respuesta sale del cache del resolver, que descuenta el tiempo transcurrido.
4. `google.com` devuelve varias IPs (o una distinta según la región). Sirve para repartir carga y tener redundancia si una falla.
5. Sí, la segunda consulta tarda ~0-1 ms contra decenas de ms la primera. Cachean el resolver local (`systemd-resolved` en 127.0.0.53), el del router o el ISP, y el resolver público.

### Ej. 3
1. (E) Ctrl+C en el cliente cierra la conexión y el `nc -l` termina (llega FIN). Si se cierra el servidor, el cliente también termina, porque detecta EOF.
2. (E) `ss -tnp | grep 8080` muestra dos líneas, una por cada extremo: `127.0.0.1:8080 ↔ 127.0.0.1:5xxxx` y al revés. Cuádrupla: IP origen, puerto origen (efímero), IP destino, puerto destino 8080.
3. (P) Un segundo cliente "conecta", porque el kernel completa el handshake y lo deja en la cola de `listen`, pero `nc -l` atiende un solo `accept()`: lo que escriba el segundo no aparece. Para atender a varios hace falta un servidor concurrente.
4. (P) En Debian/Ubuntu el `nc` usa `SO_REUSEPORT`, así que no falla (ver arriba). Lo normal (con Python o con otro `nc`) es `Address already in use`.
5. Porque `127.0.0.1` lo hace accesible solo desde mi máquina, y así no expongo a la red un servidor de desarrollo sin seguridad ni autenticación.

### Ej. 4 (E; acá el proxy devolvió `403`)
1. `HTTP/1.1 200 OK`.
2. Headers típicos: `Content-Type: text/html` (tipo del cuerpo), `Content-Length: N` (bytes del cuerpo), `Date` (hora del servidor) y `Cache-Control`/`Age` (cuánto se puede cachear).
3. Sin `Host:` el servidor responde `400 Bad Request`. HTTP/1.1 lo exige porque en una misma IP hay muchos sitios (virtual hosting) y el servidor necesita saber cuál pedís.
4. `404 Not Found` (algunos CDNs devuelven 200 igual, depende del sitio).
5. Muchos servidores toleran `\n`, otros responden 400 o se quedan esperando. El estándar dice `\r\n`. Depender de la tolerancia hace que el cliente funcione con un servidor y falle con otro (o detrás de un proxy), y además las diferencias de parseo entre equipos son fuente de ataques (request smuggling).

### Ej. 5: diagrama esperado (E, no hay tcpdump)
```
cliente:5xxxx                    servidor:8080
   | --- [S]  seq=x -----------------> |   1) SYN
   | <-- [S.] seq=y ack=x+1 ---------- |   2) SYN-ACK
   | --- [.]  ack=y+1 ---------------> |   3) ACK  (handshake listo)
   | --- [P.] length 5 "test\n" -----> |   datos
   | <-- [.]  ack ------------------- |
   | --- [F.] -----------------------> |   cierre (FIN del cliente)
   | <-- [F.] ----------------------- |   FIN del servidor (a veces junto con el ACK)
   | --- [.]  -----------------------> |   último ACK
```
2. Son unos 8 a 10 paquetes para 5 bytes de datos. Cada uno lleva además 40+ bytes de cabeceras IP/TCP, así que el overhead es enorme para mensajes chicos.
3. En el cierre aparece `[F.]` (FIN+ACK) de cada lado y un `[.]` final. Si alguien cierra con datos sin leer, puede aparecer `[R]` (RST).

### Ej. 6 (obligatorio)
1. (P) Llegaron juntos: `HOLACOMOESTAS` en un solo `recv`. No se distinguen los tres envíos.
2. (P) Con `sleep(1)`, el servidor en Python vio 3 `recv` separados (con `od -c` no se nota). Pero no se puede confiar: depende del timing, de Nagle, de la carga del servidor, de la red y de los buffers. Si el servidor tarda en leer, igual se juntan, y por la red un mensaje también puede partirse en dos. `sleep` solo esconde el problema y además hace todo más lento.
3. No es un bug. El contrato de TCP es entregar un **flujo de bytes** confiable y en orden, no mensajes. Los límites de `send()` no forman parte del contrato: el kernel puede juntar o partir segmentos como quiera.
4. Dos formas de delimitar:
   - **Delimitador** (ej. `\n`): se lee hasta encontrarlo. Si el mensaje contiene el delimitador, se corta mal, así que hay que escaparlo (como `\\n`) o codificar el contenido (base64/JSON).
   - **Prefijo de longitud** (ej. 4 bytes big-endian con el largo y después los datos): se lee el largo y después exactamente esa cantidad de bytes. El contenido puede tener cualquier byte sin problema. El riesgo es otro: un largo corrupto o malicioso (ej. 4 GB) desincroniza todo o agota la memoria, así que hay que validar un máximo.
5. (P) Se ejecutaron 3 `recvfrom`, uno por cada `sendto`. En TCP hubo 1 `recv` para 3 `send`.
6. UDP es orientado a **datagramas**: cada `sendto` es un paquete independiente que llega entero o no llega, y el kernel nunca los mezcla. TCP garantiza orden y confiabilidad de un flujo, y para eso retransmite, agrupa y re-segmenta, así que los límites originales se pierden.
7. Porque UDP no tiene conexión: no hay handshake que aceptar ni socket nuevo por cliente. El mismo socket recibe datagramas de cualquiera, y `recvfrom` dice de quién vino cada uno.

### Ej. 7
1. (P) `32768 60999`. Linux usa su propio rango desde antes de la recomendación de IANA (RFC 6335, 2011). Es más grande (~28 mil puertos contra ~16 mil) y deja libres los puertos altos (61000+), que se usaban históricamente para el masquerading/NAT. IANA solo *recomienda*: cada sistema elige, y se configura con `sysctl net.ipv4.ip_local_port_range`. Por eso no hay que asumir el rango del estándar (por ejemplo, en reglas de firewall).
2. (P) Contra un servidor local salieron 42568, 42578, 42582, 42592 y 42600: dentro del rango, crecientes y siempre pares (los kernels nuevos prefieren pares para `connect` y dejan los impares para `bind`), con un punto de partida aleatorio.
3. (P) En mi caso, IPv4 (tupla de 2 elementos `(ip, puerto)`). Con IPv6 sería `(ip, puerto, flowinfo, scope_id)`. Acá no hay IPv6, así que forzarlo da error.
4. (E) `ss -tn state established` muestra 5 líneas con el mismo destino y distinto puerto local: cada cuádrupla es única.
5. Hacia el **mismo** servidor y puerto, como mucho ~28.232 conexiones simultáneas por cada IP de origen (el tamaño del rango), porque lo único que varía es el puerto local. Hacia servidores **distintos**, el mismo puerto local se puede reusar porque la cuádrupla igual es distinta: ~28 mil *por destino*, y el límite pasa a ser la memoria o los file descriptors. Un balanceador habla siempre con los mismos pocos backends, y por eso se le agotan los puertos.

### Adicionales
- **Escaneo**: `nc -z` debería encontrar los mismos puertos que `ss -tlnp` muestra en `127.0.0.1`/`0.0.0.0`. Se escanea solo `127.0.0.1` (el host está fijo en el script).
- **Transferencia**: `nc -l 8080 > copia` en una terminal y `nc -N localhost 8080 < archivo` en otra. Verificado con `md5sum` (P).
- **Costo del handshake**: local ~0.05-0.1 ms (P), porque es solo el kernel, sin red. Hacia un remoto real se espera aproximadamente 1 RTT (decenas de ms): `create_connection` vuelve cuando llega el SYN-ACK, así que la diferencia es la latencia de ida y vuelta (distancia física, saltos, colas). El DNS se midió aparte para no mezclarlo.

## Salteado

Nada de `ejercicios.md`. `extra_manijas.md` no se hizo (por consigna).
