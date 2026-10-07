#!/usr/bin/env bash
# Clase 15 - comandos de terminal (netcat UDP, MTU y tc netem).
# Uso: bash comandos.sh <funcion>
# Las funciones de tc necesitan sudo y MODIFICAN la interfaz lo:
# siempre se saca la regla al final (trap), aunque se corte con Ctrl+C.

PUERTO=${PUERTO:-8080}

# Ej 1.2: nc como servidor UDP. En otra terminal:
#   python3 ej1_echo_udp.py cliente --port $PUERTO
nc_servidor() {
    nc -u -l "$PUERTO"
}

# Ej 1.1 / 1.2: nc como cliente UDP contra ej1_echo_udp.py servidor
nc_cliente() {
    nc -u localhost "$PUERTO"
}

# Ej 6.1: MTU de las interfaces (con ip si está; si no, desde /sys)
mtu() {
    if command -v ip >/dev/null; then
        ip link show | grep mtu
    else
        for i in /sys/class/net/*; do echo "$(basename "$i"): mtu $(cat "$i/mtu")"; done
    fi
}

# Ej 3 parte A (3b): pérdida y desorden REALES en loopback
perdida_real() {
    command -v tc >/dev/null || { echo "tc no está instalado (paquete iproute2)"; return 1; }
    trap 'sudo tc qdisc del dev lo root 2>/dev/null' EXIT INT
    sudo tc qdisc add dev lo root netem loss 20% reorder 25% 50% delay 1ms
    python3 ej3_perdidas.py 0
    sudo tc qdisc del dev lo root
    trap - EXIT INT
}

# Ej 6.4 / 6.5: fragmentación con pérdida real del 5%.
# OJO: en lo el MTU es 65536 y no fragmenta; para ver el efecto se baja
# temporalmente el MTU de lo a 1500 y se restaura al final.
fragmentacion_real() {
    command -v tc >/dev/null || { echo "tc no está instalado (paquete iproute2)"; return 1; }
    local mtu_orig; mtu_orig=$(cat /sys/class/net/lo/mtu)
    trap 'sudo tc qdisc del dev lo root 2>/dev/null; sudo ip link set lo mtu '"$mtu_orig" EXIT INT
    sudo ip link set lo mtu 1500
    sudo tc qdisc add dev lo root netem loss 5%
    python3 ej6_mtu.py --perdida 0 --veces 20
    sudo tc qdisc del dev lo root
    sudo ip link set lo mtu "$mtu_orig"
    trap - EXIT INT
}

if [[ $# -gt 0 ]]; then
    "$@"
fi
