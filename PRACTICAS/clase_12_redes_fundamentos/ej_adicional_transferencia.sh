#!/usr/bin/env bash
# Ejercicio adicional: servidor de archivos improvisado con nc + verificación md5sum.
# Uso: ./ej_adicional_transferencia.sh [archivo] [puerto]
# Hace todo en una sola terminal: el receptor queda en segundo plano.
set -eu
ORIGEN=${1:-/etc/services}
PUERTO=${2:-8080}
DESTINO=$(mktemp)

# Receptor: escucha y guarda todo lo que llega (en la consigna sería otra terminal)
nc -l "$PUERTO" > "$DESTINO" &
RECEPTOR=$!
sleep 0.5

# Emisor: -N cierra el lado de escritura al terminar el archivo (EOF -> FIN)
nc -N localhost "$PUERTO" < "$ORIGEN"
wait "$RECEPTOR"

echo "md5 origen : $(md5sum < "$ORIGEN")"
echo "md5 destino: $(md5sum < "$DESTINO")"
if cmp -s "$ORIGEN" "$DESTINO"; then
    echo "OK: el archivo llegó íntegro ($(wc -c < "$DESTINO") bytes)"
else
    echo "ERROR: los archivos difieren"
fi
rm -f "$DESTINO"
