# Bloque 0 — IPv6

Los scripts `explorar_ipv6.py` y `dual_stack.py` son de la cátedra (están en
`bloque_0_autonomo/ipv6/` del repo de la materia); acá van las soluciones propias.
Todos los servidores usan el puerto 8080 por default (como la consigna) y aceptan otro
por argumento.

## Ejercicios

| Ejercicio | Archivo(s) | Cómo correrlo (desde esta carpeta) |
|---|---|---|
| 1. Leer y escribir direcciones | `ej1_direcciones.py` | `python3 ej1_direcciones.py` |
| 2. Direcciones de tu máquina | `comandos_ej2.sh`, `ej2_getsockname.py` | `EXPLORAR=/ruta/a/explorar_ipv6.py bash comandos_ej2.sh eth0` · `python3 ej2_getsockname.py` |
| **3. Servidor dual-stack (obligatorio)** A-C | `ej3_servidor.py` | `python3 ej3_servidor.py --modo v4\|dual\|v6only [--port 8080]` |
| 3 D. Normalizar | `ej3_servidor.py` (`normalizar()`) | `python3 -c "from ej3_servidor import normalizar; print(normalizar('::ffff:127.0.0.1'))"` |
| 3 E. Cliente agnóstico | `ej3_cliente.py` (`conectar()`) | `python3 ej3_cliente.py localhost --port 8080` (o `127.0.0.1`, `::1`) |
| 3 todo junto | `ej3_prueba.sh` | `bash ej3_prueba.sh 8080` |
| 4. getaddrinfo en detalle | `ej4_getaddrinfo.py` | `python3 ej4_getaddrinfo.py google.com` |
| 5. UDP sobre IPv6 | `echo_udp6.py` | `python3 echo_udp6.py servidor 8080` y en otra terminal `python3 echo_udp6.py cliente 8080 hola` |
| 6. Diferencias del protocolo | — | teórico, ver Respuestas |
| Adicional: migrar server_threads | `server_threads_dual.py` | `python3 server_threads_dual.py 8080` y `nc ::1 8080` / `nc 127.0.0.1 8080` |
| Adicional: vecinos link-local | `adicionales.sh` | `bash adicionales.sh eth0` |
| Adicional: comparar encabezados | `adicionales.sh` | `sudo bash adicionales.sh eth0` (usa tcpdump) |
| Adicional: servidor que reporta la familia | `servidor_familia.py` | `python3 servidor_familia.py --port 8080` y `python3 ej3_cliente.py ::1 -p 8080` |

## Respuestas

### Ejercicio 1

1. `2001:0db8:0000:0000:0000:ff00:0042:8329` → `2001:db8::ff00:42:8329`
2. `0000:...:0001` → `::1`
3. `fe80:0000:0000:0000:0202:b3ff:fe1e:8329` → `fe80::202:b3ff:fe1e:8329`
4. `2001:0db8:0000:0000:0001:0000:0000:0001` → `2001:db8::1:0:0:1`
   (las dos secuencias son de 2 grupos: se comprime la **primera**, la otra queda como `0:0`).
5. `::` significa "la cantidad de grupos de ceros que falte para llegar a 8". Con dos `::`
   no hay forma de saber cómo repartirlos. En `2001:db8::1::1` hay 4 grupos escritos y faltan 4:
   - `2001:db8:0:1:0:0:0:1` (1 + 3),
   - `2001:db8:0:0:1:0:0:1` (2 + 2),
   - `2001:db8:0:0:0:1:0:1` (3 + 1). Por eso es inválida (ipaddress la rechaza).
6. `::1` → `0000:0000:0000:0000:0000:0000:0000:0001`
7. `2001:db8::8a2e:370:7334` → `2001:0db8:0000:0000:0000:8a2e:0370:7334`
8. `ff02::1` → `ff02:0000:0000:0000:0000:0000:0000:0001`
9. `2001:db8::/32` es el rango **reservado para documentación** (RFC 3849): nunca se rutea en
   Internet, por eso la stdlib da `is_private=True` / `is_global=False` y el explorador la
   clasifica como reservada/privada.
10. `is_global` en la stdlib significa básicamente "no está en el registro de rangos de propósito
   especial de IANA", y `ff00::/8` (multicast) no figura ahí, así que da `True`. Pero `ff02::1`
   es multicast de alcance *link-local*: jamás sale del enlace. Conclusión: los flags se solapan
   y no hay que confiar en uno solo; hay que preguntar de lo específico a lo general
   (mapeada → loopback → multicast → link-local → global).

### Ejercicio 2

1-4. Depende de cada máquina. Lo típico en Linux: `::1/128` con scope `host`, una `fe80::/64`
   (scope `link`) por cada interfaz con IPv6, y si el ISP da IPv6, una o más de scope `global`
   (una estable y otras temporales de privacidad). Con Docker aparecen muchas `fe80::` porque
   cada `veth` de cada contenedor y cada bridge (`docker0`, redes de compose) es una interfaz
   y **toda interfaz IPv6 se autoasigna su link-local**. Tener dirección global no implica
   tener ruta: eso se ve por separado con la sección 3 (direcciones) y 6 (ruta) del explorador,
   o con `ip -6 route show default`. Con un `/64` quedan **64 bits para hosts** (2⁶⁴ ≈ 1,8·10¹⁹
   direcciones) contra 8 bits en una `/24` IPv4 (254 hosts usables).
   *En esta máquina de pruebas* el kernel no tiene IPv6 (no existe `/proc/net/if_inet6`,
   `socket(AF_INET6)` da `Errno 97 Address family not supported`) ni están `ip`/`ping6`, así que
   no hay direcciones IPv6 para contar.
5. `ping6 fe80::1` falla (según la versión: `connect: Invalid argument` o un aviso de que la
   link-local "requiere ifname o scope-id"). Es ambigua porque **todas** las interfaces tienen
   el prefijo `fe80::/64`: el kernel no sabe por cuál enlace mandar el paquete.
6. Con `fe80::1%eth0` se indica la interfaz (scope ID) y el ping sale por ahí (responde si hay
   un equipo con esa dirección en ese enlace, típicamente el router).
7. `getsockname()` en IPv6 devuelve `(dirección, puerto, flowinfo, scope_id)`: flowinfo es la
   etiqueta de flujo (casi siempre 0) y scope_id el índice de la interfaz (0 salvo link-local).
8. `host, puerto = sock.getsockname()` con un socket IPv6 tira
   `ValueError: too many values to unpack (expected 2)`. Para que ande con las dos familias:
   `host, puerto = sock.getsockname()[:2]` (lo muestra `ej2_getsockname.py`).

### Ejercicio 3 (obligatorio)

1. Cliente IPv4 contra el servidor `AF_INET` en `0.0.0.0`: conecta.
2. Cliente `::1`: `ConnectionRefusedError`. El socket es `AF_INET`: solo escucha en IPv4, y en
   el puerto IPv6 no hay nadie escuchando, así que el kernel responde con RST.
3. `s.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 0)` (en `ej3_servidor.py --modo dual`).
   Con eso conectan las dos familias.
4. El servidor ve al cliente IPv4 como **`::ffff:127.0.0.1`**.
5. Prefijo `::ffff:0:0/96`: son las **direcciones IPv4 mapeadas en IPv6** (*IPv4-mapped IPv6
   addresses*): 80 bits en 0, 16 en 1 y los 32 bits de la IPv4.
6. Con `IPV6_V6ONLY=1` el cliente IPv4 recibe `Connection refused`: el socket solo acepta IPv6
   (para IPv4 haría falta un segundo socket `AF_INET` en el mismo puerto).
7. `cat /proc/sys/net/ipv6/bindv6only` → en Linux suele dar `0` (dual-stack por default).
8. Porque el default depende del sistema: Windows y los BSD traen `1` (OpenBSD ni siquiera
   soporta dual-stack) y en Linux se puede cambiar por sysctl. Si no lo ponés explícito, el
   mismo código a un compañero no le atiende IPv4. Explícito = mismo comportamiento en todos lados.
9. `normalizar()` está en `ej3_servidor.py` (usa `ipaddress.ip_address(h).ipv4_mapped`).
10. Porque una lista de bloqueo con `1.2.3.4` no coincide con el string `::ffff:1.2.3.4`: el
   atacante entraría igual solo porque el servidor es dual-stack. Lo mismo con logs, rate
   limiting o estadísticas por IP: hay que comparar la forma normalizada.
11. `conectar()` está en `ej3_cliente.py`: recorre todo `getaddrinfo()`, intenta crear el socket
   y conectar, y ante `OSError` sigue con la próxima; si ninguna anda, relanza el último error.
12. Con `localhost`, en un Linux típico vienen **`::1` primero y después `127.0.0.1`** (RFC 6724
   prefiere IPv6). En esta máquina solo vino `127.0.0.1` porque no hay IPv6.
13. Acá (`explorar_ipv6.py resolver google.com` y `ej4_getaddrinfo.py`) vinieron **primero las
   IPv4 y después las IPv6**, aunque el DNS sí devolvió registros AAAA: como el sistema no
   tiene ruta (ni soporte) IPv6, el ordenamiento de RFC 6724 de glibc baja las IPv6 al final.
   Con ruta IPv6 real aparecerían primero.
14. Porque tener una dirección no garantiza poder llegar: la primera puede ser IPv6 sin ruta,
   un servidor caído de un pool round-robin, o un firewall. Si solo probás la primera, el
   programa falla aunque otra dirección del mismo nombre ande perfecto (es la idea de
   *Happy Eyeballs*, que además lo hace en paralelo para no esperar timeouts).

### Ejercicio 4

1. Sí, funciona: `getaddrinfo` traduce el nombre de servicio a puerto usando la base de
   servicios (`/etc/services`, vía NSS); `socket.getservbyname('http')` da 80.
2. Por ejemplo: `ssh 22/tcp`, `domain 53/tcp`(DNS), `https 443/tcp`, `smtp 25/tcp`,
   `postgresql 5432/tcp`.
3. Con `AF_INET6` solo vienen las AAAA: acá dio **4 resultados** para google.com (con
   `SOCK_STREAM`; sin filtrar por tipo serían 3 por dirección: stream, dgram y raw).
4. Un nombre inexistente tira **`socket.gaierror: [Errno -2] Name or service not known`**
   (EAI_NONAME). Es subclase de `OSError`.
5. No cambia nada: `AF_UNSPEC` vale 0 y es justamente el default de `family`. (Las IPs exactas
   pueden variar entre dos consultas porque el DNS rota las respuestas, pero las familias y
   la cantidad son las mismas.)

### Ejercicio 5

1. `echo_udp6.py`.
2. No: solo `AF_INET` → `AF_INET6` y `0.0.0.0`/`localhost` → `::1`. `sendto`, `recvfrom`,
   timeouts y lógica quedan iguales (respondemos con `sendto(datos, origen)` pasando la tupla
   tal cual, así que no importa cuántos elementos tenga).
3. `recvfrom()` devuelve como origen una tupla de **4 elementos** `(host, puerto, flowinfo,
   scope_id)`, contra 2 en IPv4.
4. Porque IPv6 **eliminó el checksum del encabezado de red**. En IPv4, aunque UDP no tuviera
   checksum, el encabezado IP al menos protegía las direcciones; en IPv6 nada protegería
   direcciones ni datos si UDP tampoco lo hiciera, y un paquete con la dirección corrupta
   podría entregarse al destino equivocado. Por eso RFC 8200 hace obligatorio el checksum UDP
   (que incluye un pseudo-encabezado con las direcciones de origen y destino).

### Ejercicio 6

1. Con tamaño fijo, el router sabe exactamente dónde está cada campo y dónde empieza el
   siguiente encabezado, sin leer un largo variable ni procesar opciones: el parseo es simple
   y se hace en hardware a velocidad de línea. Las opciones pasaron a encabezados de extensión
   que los routers intermedios en general no miran.
2. Porque el error ya lo detectan otras capas: el enlace (CRC de Ethernet/Wi-Fi) y el
   transporte (checksum de TCP y de UDP, ahora obligatorio). Además así el router no tiene que
   recalcular el checksum en cada salto (en IPv4 había que hacerlo porque el TTL cambia).
3. Que el path MTU discovery pasa a ser **obligatorio**: el emisor tiene que conocer el MTU
   del camino; si manda algo grande, el router lo descarta y avisa con ICMPv6 *Packet Too Big*,
   y el emisor achica (o fragmenta él mismo). Si eso falla, el emisor puede quedarse en 1280.
4. Para que siempre haya un tamaño "seguro" razonable sin fragmentar: con encabezados más
   grandes (40 bytes + extensiones) y routers que no fragmentan, un piso de 576 desperdiciaría
   mucho. Todos los enlaces modernos aguantan 1280 (y los que no, tienen que fragmentar por
   debajo, en la capa de enlace), dejando margen para túneles sobre Ethernet de 1500.
5. En IPv6 ICMPv6 no es "solo diagnóstico": lleva funciones esenciales. Si se bloquea entero se
   rompen, entre otras: el **Neighbor Discovery** (NS/NA, el reemplazo de ARP: sin eso no se
   resuelve la MAC del vecino ni anda la detección de direcciones duplicadas), la
   **autoconfiguración SLAAC** (Router Solicitation/Advertisement: no hay prefijo ni ruta por
   defecto) y el **path MTU discovery** (Packet Too Big: conexiones que se cuelgan con paquetes
   grandes, los "agujeros negros"). En IPv4, ARP no es ICMP y los routers fragmentaban, por eso
   bloquear ICMP "casi" no se notaba.

### Adicionales

- **Migrar server_threads.py:** cambiaron **3 líneas** (marcadas `# DUAL`): `HOST='::'`,
  `AF_INET` → `AF_INET6` y la línea nueva del `setsockopt(IPV6_V6ONLY, 0)` (más el print).
- **Vecinos link-local:** `ip -6 neigh` muestra solo los vecinos con los que ya hubo tráfico;
  después de `ping6 ff02::1%iface` (todos los nodos del enlace) la tabla se llena con todos los
  que respondieron. Es la forma IPv6 de "barrer" la red, porque escanear una /64 dirección
  por dirección es imposible.
- **Comparar encabezados:** mandando 10 bytes por UDP, tcpdump muestra un largo total de
  38 bytes en IPv4 (20 IP + 8 UDP + 10) y en IPv6 la longitud de payload de 18 con un encabezado
  fijo de 40 (58 en total): el encabezado IPv6 es el doble, pero fijo.
- **Servidor que reporta la familia:** `servidor_familia.py` le contesta al cliente la familia,
  cómo lo ve (normalizado y, si llegó mapeado, lo aclara), a qué dirección local habló y,
  en IPv6, flowinfo y scope_id. Si el sistema no tiene IPv6 cae a un socket IPv4.

## Qué se probó

**Limitación del entorno:** la máquina donde se hicieron las pruebas tiene un kernel **sin
soporte IPv6** (ni siquiera `::1`: `socket(AF_INET6)` da `Errno 97`), y no tiene `ip`, `ping6`
ni `tcpdump`. Por eso:

- Probado OK: `ej1_direcciones.py` (todo verificado con `ipaddress`), `ej2_getsockname.py`
  (parte IPv4; la IPv6 informa el error limpio), `ej3_servidor.py --modo v4` + `ej3_cliente.py`
  (Parte A: IPv4 conecta, `::1` falla), el reintento del cliente sobre todas las direcciones,
  `normalizar()` con varios casos, `ej4_getaddrinfo.py` (el DNS sí responde AAAA: se vio el
  reordenamiento IPv4-primero), `servidor_familia.py` (fallback IPv4 y `describir()` con tuplas
  IPv6 simuladas). Los scripts `.sh` corren y avisan cuando falta una herramienta.
- **No se pudo probar** (necesita IPv6 en el kernel): servidor dual/v6only (Partes B y C),
  `echo_udp6.py`, `server_threads_dual.py`, las partes de ping6/vecinos/tcpdump. El código
  sigue el mismo patrón que `dual_stack.py` de la cátedra; en cualquier Linux con IPv6
  `bash ej3_prueba.sh` muestra las tres partes de una.
