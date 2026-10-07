#!/usr/bin/env bash
# Ejercicio 3: corre las Partes A, B y C levantando el servidor en background
# y probando con clientes de las dos familias. Uso: bash ej3_prueba.sh [puerto]
cd "$(dirname "$0")"
PUERTO=${1:-8080}

prueba() {   # $1 = modo, resto = hosts a probar
    local modo=$1; shift
    echo; echo "=========== Servidor --modo $modo (puerto $PUERTO) ==========="
    python3 ej3_servidor.py --modo "$modo" --port "$PUERTO" &
    local pid=$!
    sleep 0.5
    for host in "$@"; do
        echo "--- cliente -> $host"
        timeout 5 python3 ej3_cliente.py "$host" --port "$PUERTO"
    done
    kill "$pid" 2>/dev/null; wait "$pid" 2>/dev/null
}

prueba v4     127.0.0.1 ::1      # Parte A: ::1 falla (el socket es solo AF_INET)
prueba dual   127.0.0.1 ::1      # Parte B: las dos andan; IPv4 llega como ::ffff:127.0.0.1
prueba v6only 127.0.0.1 ::1      # Parte C: IPv4 rechazado
prueba dual   localhost          # Parte E: orden de getaddrinfo para localhost

echo; echo "Default del sistema (Parte C.7):"
cat /proc/sys/net/ipv6/bindv6only 2>/dev/null || echo "  (no existe: el kernel no tiene IPv6)"
