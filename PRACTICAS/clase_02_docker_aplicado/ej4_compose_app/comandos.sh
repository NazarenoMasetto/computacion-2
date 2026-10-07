#!/usr/bin/env bash
# Ejercicio 4 - Docker Compose. Correr desde ej4_compose_app/:  bash comandos.sh
# (La consigna usa "docker-compose" con guión; acá usamos "docker compose",
#  que es el comando actual. Hacen lo mismo.)
set -u
cd "$(dirname "$0")"

echo "== 4.1 App con Redis =="
# En la consigna se usa "docker compose up" en primer plano y se corta con Ctrl+C.
# Acá lo levantamos en background (-d) para poder seguir con las tareas.
docker compose up -d --build
sleep 7
docker compose ps                 # tarea 1: estado
docker compose logs redis         # tarea 2: solo logs de redis
docker compose logs app
# Tarea 3: detener y volver a levantar (equivale a Ctrl+C y "up" de nuevo).
# "stop" mantiene el contenedor de redis -> el contador SIGUE.
docker compose stop
docker compose up -d
sleep 5
docker compose logs --tail 3 app
# "down" borra los contenedores -> el contador vuelve a 1.
docker compose down
docker compose up -d
sleep 5
docker compose logs --tail 3 app
docker compose down

echo "== 4.2 Persistencia =="
F=docker-compose.persistencia.yml
docker compose -f $F down
docker compose -f $F up -d --build
sleep 7
docker compose -f $F logs --tail 2 app
docker compose -f $F down
docker compose -f $F up -d
sleep 5
docker compose -f $F logs --tail 3 app      # el contador continúa
docker compose -f $F down                   # "down -v" borraría también el volumen

echo "== 4.3 Hot reload =="
F=docker-compose.dev.yml
docker compose -f $F up -d --build
sleep 5
docker compose -f $F logs --tail 2 app
# Editá app.py y después:
#   docker compose -f docker-compose.dev.yml restart app
docker compose -f $F down
