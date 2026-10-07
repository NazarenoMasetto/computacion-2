#!/usr/bin/env bash
# Ejercicio 5 - Proyecto integrador. Correr desde ej5_proyecto/:  bash comandos.sh
# Puerto en el host: WEB_PORT (default 8000).
set -u
cd "$(dirname "$0")"
PUERTO=${WEB_PORT:-8000}
export WEB_PORT=$PUERTO

docker compose up -d --build
sleep 5
docker compose ps
echo "--- Primera request ---"
curl -s "http://localhost:$PUERTO/"
sleep 3
echo "--- 3 segundos después (el contador del worker avanzó) ---"
curl -s "http://localhost:$PUERTO/"
docker compose logs --tail 5 worker
docker compose down        # "down -v" borra también el volumen de Redis
