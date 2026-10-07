#!/usr/bin/env bash
# Ejercicios adicionales de terminal (IPv6). Solo leen/capturan, no cambian nada.
# Uso: bash adicionales.sh [interfaz]      (default eth0)
# tcpdump necesita root: correlo con sudo si querés la parte de encabezados.
IFAZ=${1:-eth0}
corre() { echo; echo "\$ $*"; "$@" || echo "   (falló con código $?)"; }

echo "=========== Escáner de vecinos link-local ==========="
# Tabla de vecinos (el reemplazo de ARP en IPv6, vía Neighbor Discovery)
corre ip -6 neigh show
# Ping a ff02::1 = todos los nodos del enlace. Después de esto la tabla
# de vecinos se llena con los que respondieron.
corre ping6 -c2 -W2 "ff02::1%$IFAZ"
corre ip -6 neigh show dev "$IFAZ"

echo; echo "=========== Comparar encabezados (tcpdump sobre lo) ==========="
# Capturamos 4 paquetes de cada familia mientras mandamos un datagrama UDP
# de 10 bytes a 127.0.0.1 y a ::1. En la salida, 'length' de IP/IP6:
#   IPv4: 20 (IP) + 8 (UDP) + 10 = 38 bytes
#   IPv6: 40 (IP6) + 8 (UDP) + 10 = 58 bytes
PUERTO=${PUERTO:-21999}
if command -v tcpdump >/dev/null; then
    timeout 5 tcpdump -i lo -n -v -c 1 "ip and udp port $PUERTO" &
    sleep 1; python3 -c "import socket;socket.socket(socket.AF_INET,socket.SOCK_DGRAM).sendto(b'0123456789',('127.0.0.1',$PUERTO))"
    wait
    timeout 5 tcpdump -i lo -n -v -c 1 "ip6 and udp port $PUERTO" &
    sleep 1; python3 -c "import socket;socket.socket(socket.AF_INET6,socket.SOCK_DGRAM).sendto(b'0123456789',('::1',$PUERTO))"
    wait
else
    echo "   (tcpdump no está instalado)"
fi
