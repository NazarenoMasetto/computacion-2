#!/usr/bin/env bash
# Ejercicio adicional: escaneo de puertos PROPIO (solo localhost) con nc -z.
# Uso: ./ej_adicional_escaneo.sh [desde] [hasta]     (default 1 1024)
# ¡Solo contra tu propia máquina! Escanear sistemas ajenos sin permiso es ilegal.
set -u
HOST=127.0.0.1               # fijo a propósito: no se acepta otro host
DESDE=${1:-1}
HASTA=${2:-1024}

echo "Puertos TCP abiertos en $HOST ($DESDE-$HASTA):"
for p in $(seq "$DESDE" "$HASTA"); do
    # -z: solo prueba la conexión sin mandar datos; -w1: timeout de 1 s
    if nc -z -w1 "$HOST" "$p" 2>/dev/null; then
        echo "  $p abierto"
    fi
done

echo
echo "Para comparar, lo que dice el kernel (ss):"
if command -v ss >/dev/null; then
    ss -tln
else
    echo "  (ss no está instalado: sudo apt install iproute2)"
fi
