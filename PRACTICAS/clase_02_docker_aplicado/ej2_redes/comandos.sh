#!/usr/bin/env bash
# Ejercicio 2 - Redes. Correr desde ej2_redes/:  bash comandos.sh
set -u
cd "$(dirname "$0")"

echo "== 2.1 Comunicación entre contenedores =="
docker network create ejercicio-red
docker run -d --name servidor --network ejercicio-red python:3.11 \
    python -m http.server 8000
sleep 2   # darle tiempo a que arranque el servidor
docker run --rm --network ejercicio-red python:3.11 \
    python -c "import urllib.request; print(urllib.request.urlopen('http://servidor:8000').read()[:100])"
docker stop servidor && docker rm servidor

echo "== 2.1 Tarea: servir MI directorio (publico/) con un volumen =="
# Montamos ./publico en /srv (solo lectura) y le decimos a http.server que sirva eso.
docker run -d --name servidor --network ejercicio-red \
    -v "$(pwd)/publico":/srv:ro python:3.11 \
    python -m http.server 8000 --directory /srv
sleep 2
docker run --rm --network ejercicio-red python:3.11 \
    python -c "import urllib.request; print(urllib.request.urlopen('http://servidor:8000/index.html').read().decode())"
docker stop servidor && docker rm servidor
docker network rm ejercicio-red

echo "== 2.2 Redis =="
docker network create redis-net
docker run -d --name redis --network redis-net redis:alpine
# Interactivo (consigna):  docker run -it --rm --network redis-net python bash
#                          pip install redis ; python ; (código de redis_prueba.py)
# Equivalente no interactivo:
docker run --rm --network redis-net -v "$(pwd)":/app -w /app python \
    sh -c "pip install -q redis && python redis_prueba.py"

echo "== 2.2 Tarea: contenedor Python NUEVO, ¿siguen los datos? =="
docker run --rm --network redis-net -v "$(pwd)":/app -w /app python \
    sh -c "pip install -q redis && python redis_leer.py"

# Limpieza al final
docker stop redis && docker rm redis
docker network rm redis-net
