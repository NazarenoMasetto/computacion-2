#!/usr/bin/env bash
# Clase 12 - Redes: comandos de terminal de los ejercicios 1 a 5 y 7.
#
# Al ejecutarlo corre SOLO los comandos de lectura (no modifican nada).
# Los que necesitan varias terminales (nc -l, tcpdump) están comentados:
# copialos a mano en el orden indicado.
#
# Uso: ./comandos.sh
# Herramientas: sudo apt install iproute2 dnsutils netcat-openbsd traceroute tcpdump
set -u
PUERTO=${PUERTO:-8080}     # puerto de la consigna; se puede cambiar: PUERTO=9000 ./comandos.sh

correr() {
    # Ejecuta el comando si la herramienta existe; si no, avisa y sigue
    echo; echo "\$ $*"
    if command -v "$1" >/dev/null 2>&1; then
        timeout 15 "$@"
    else
        echo "  ($1 no está instalado)"
    fi
}

echo "===== Ejercicio 1: reconocimiento de la máquina ====="
correr ip addr show          # 1.1 interfaces: lo (127.0.0.1) + eth0/wlan0, IPv4 privada, IPv6 fe80::
correr ip route              # 1.2 'default via X.X.X.1 dev ...' = gateway (misma subred que mi IP)
correr ss -tlnp              # 1.3 sockets TCP en LISTEN, numéricos, con proceso (-p necesita sudo para ver todos)

echo; echo "===== Ejercicio 2: DNS ====="
correr dig www.um.edu.ar     # ANSWER SECTION: IP y TTL
correr dig www.um.edu.ar     # de nuevo enseguida: el TTL bajó (viene del cache del resolver)
correr dig google.com +short # varias IPs: balanceo y redundancia
# Tiempo con y sin cache: la segunda suele dar 0-1 ms
if command -v dig >/dev/null; then
    dig google.com | grep "Query time"
    dig google.com | grep "Query time"
fi

echo; echo "===== Ejercicio 7: puertos efímeros ====="
cat /proc/sys/net/ipv4/ip_local_port_range   # Linux: 32768 60999 (IANA: 49152 65535)
echo "Conexiones establecidas (correr mientras ej7_puertos_efimeros.py espera el Enter):"
correr ss -tn state established

# -------------------------------------------------------------------------
# Lo que sigue es INTERACTIVO: copiar a mano en varias terminales.
# -------------------------------------------------------------------------

# ===== Ejercicio 3.1: conversación con netcat =====
# Terminal 1:  nc -l 8080
# Terminal 2:  nc localhost 8080          (escribir y Enter: aparece en la otra)
# Terminal 3:  ss -tnp | grep 8080        (ver la cuádrupla IP:puerto <-> IP:puerto)
# Dos clientes a la vez: un tercer 'nc localhost 8080' conecta (el kernel completa el
# handshake y lo deja en la cola de listen) pero nc -l solo atiende a UNO: lo que
# escriba el segundo no aparece.

# ===== Ejercicio 3.2: puerto ocupado =====
# Con 'nc -l 8080' corriendo, en otra terminal:  nc -l 8080
# OJO: el netcat-openbsd de Debian/Ubuntu activa SO_REUSEPORT, así que el segundo
# nc NO falla (lo comprobamos con strace). Para ver el error clásico:
#   python3 -c "import socket; s=socket.socket(); s.bind(('0.0.0.0', 8080)); s.listen()"
#   -> OSError: [Errno 98] Address already in use

# ===== Ejercicio 3.3: loopback vs todas las interfaces =====
# nc -l 127.0.0.1 8080     # solo desde la misma máquina
# nc -l 0.0.0.0 8080       # también desde otra máquina de la red: nc <mi-ip> 8080

# ===== Ejercicio 4: HTTP a mano (necesita salida a internet) =====
# printf 'GET / HTTP/1.1\r\nHost: example.com\r\nConnection: close\r\n\r\n' | nc example.com 80
# Sin Host (HTTP/1.1 lo exige -> 400 Bad Request):
# printf 'GET / HTTP/1.1\r\nConnection: close\r\n\r\n' | nc example.com 80
# Recurso inexistente (-> 404 Not Found):
# printf 'GET /noexiste HTTP/1.1\r\nHost: example.com\r\nConnection: close\r\n\r\n' | nc example.com 80
# Solo \n (algunos servidores lo toleran, otros responden 400):
# printf 'GET / HTTP/1.1\nHost: example.com\nConnection: close\n\n' | nc example.com 80

# ===== Ejercicio 5: handshake con tcpdump (root) =====
# Terminal 1:  sudo tcpdump -i lo -n port 8080
# Terminal 2:  nc -l 8080
# Terminal 3:  echo "test" | nc -N localhost 8080
# Esperado: [S] / [S.] / [.] (handshake), [P.] length 5 ("test\n"), [.] ACK,
#           y el cierre con [F.] / [.] / [F.] / [.] (o [F.] combinados).

# ===== Ejercicio 6: ver README y los .py de esta carpeta =====
# Terminal 1:  nc -l 8080 | od -c            o   python3 ej6_servidor_tcp.py
# Terminal 2:  python3 ej6_cliente_tcp.py    y   python3 ej6_cliente_tcp.py --pausa 1
# UDP:         python3 udp_srv.py   +   python3 ej6_cliente_udp.py
