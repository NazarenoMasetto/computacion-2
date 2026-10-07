#!/usr/bin/env bash
# Clase 1 - Docker Intro: comandos de los ejercicios 1 a 5 y síntesis.
#
# Uso: correr desde esta carpeta ->  bash comandos.sh
# Los pasos interactivos (docker run -it ...) quedan comentados con su
# equivalente NO interactivo al lado, así el script corre de punta a punta.
# Todos los contenedores que se crean llevan la etiqueta "curso=c2-clase01"
# y al final se borran SOLO esos (no se toca nada del usuario).

set -u
ETIQ="curso=c2-clase01"
cd "$(dirname "$0")"

titulo() { echo; echo "########## $* ##########"; }

titulo "Prerequisito: docker funcionando"
docker run --rm hello-world | head -3

# ---------------------------------------------------------------
titulo "Ejercicio 1.1: primer contenedor (ubuntu)"
# Interactivo (como pide la consigna):
#   docker run -it ubuntu bash
#   cat /etc/os-release ; whoami ; ps aux ; ls /
#   apt update && apt install -y cowsay
#   /usr/games/cowsay "Hola desde Docker"
#   exit
# Equivalente no interactivo:
docker run --label "$ETIQ" ubuntu bash -c '
  grep PRETTY_NAME /etc/os-release
  whoami
  ps aux
  ls /
  apt-get update -qq && apt-get install -y -qq cowsay > /dev/null
  /usr/games/cowsay "Hola desde Docker"
'

titulo "Ejercicio 1.2: el contenedor es efímero"
# docker run -it ubuntu bash   y adentro:  /usr/games/cowsay "Hola"
docker run --label "$ETIQ" ubuntu bash -c '/usr/games/cowsay "Hola" || echo "-> cowsay NO existe: es un contenedor nuevo"'

titulo "Ejercicio 1.3: ver contenedores"
docker ps                                    # solo los que están corriendo
docker ps -a --filter "label=$ETIQ"          # los que creó este script (detenidos)
echo "Contenedores creados por este script: $(docker ps -aq --filter "label=$ETIQ" | wc -l)"

# ---------------------------------------------------------------
titulo "Ejercicio 2.1: Python interactivo"
# docker run -it python      (y adentro el código de la consigna)
docker run --rm python python -c '
import sys, os, json
print(f"Python {sys.version}")
print(f"Sistema: {os.uname()}")
data = {"nombre": "Docker", "año": 2026}
print(json.dumps(data, indent=2))
'

titulo "Ejercicio 2.2: ejecutar un comando Python"
docker run --rm python python -c "print('Hola desde contenedor')"
docker run --rm python python -c "import platform; print(platform.platform())"

titulo "Ejercicio 2.3: diferentes versiones de Python"
docker run --rm python:3.11 python --version
docker run --rm python:3.9 python --version
docker run --rm python:3.8-slim python --version
echo -n "Local: "; python3 --version

# ---------------------------------------------------------------
titulo "Ejercicio 3.2: ejecutar hola.py montando el directorio"
docker run --rm -v "$(pwd)":/app -w /app python python hola.py

titulo "Ejercicio 3.3: crear un archivo desde el contenedor"
docker run --rm -v "$(pwd)":/app -w /app python python -c "
with open('desde_docker.txt', 'w') as f:
    f.write('Este archivo fue creado dentro del contenedor\n')
print('Archivo creado')
"
cat desde_docker.txt
ls -l desde_docker.txt     # ojo: el dueño es root (el usuario del contenedor)

# ---------------------------------------------------------------
titulo "Ejercicio 4.1: contenedores en background"
docker run -d --label "$ETIQ" --name mi-python python sleep 300
docker ps --filter name=mi-python
docker logs mi-python
# Con -it si lo corrés a mano; acá sin -it porque no hay terminal:
docker exec mi-python python -c "print('Hola desde el contenedor en background')"
docker stop mi-python
docker rm mi-python

titulo "Ejercicio 4.2: limpieza"
docker ps -a
# La consigna usa:  docker container prune   (borra TODOS los detenidos,
# incluso los que no son de este script). Por seguridad acá borramos
# solo los nuestros filtrando por etiqueta:
docker container prune -f --filter "label=$ETIQ"
docker images
# Opcional (pregunta antes de borrar):  docker image prune

# ---------------------------------------------------------------
titulo "Ejercicio 5.1: script con dependencias (falla: no está requests)"
docker run --rm -v "$(pwd)":/app -w /app python python con_dependencias.py \
  || echo "-> Falló como se esperaba (ModuleNotFoundError: requests)"

titulo "Ejercicio 5.2: solución temporal (pip install en cada corrida)"
docker run --rm -v "$(pwd)":/app -w /app python sh -c "pip install -q requests && python con_dependencias.py"

# ---------------------------------------------------------------
titulo "Síntesis: info_sistema.py en local, python:3.11 y python:3.9"
echo "--- LOCAL ---";        python3 info_sistema.py
echo "--- python:3.11 ---";  docker run --rm -v "$(pwd)":/app -w /app python:3.11 python info_sistema.py
echo "--- python:3.9 ---";   docker run --rm -v "$(pwd)":/app -w /app python:3.9  python info_sistema.py

# Limpieza final: solo contenedores de este script
docker rm -f $(docker ps -aq --filter "label=$ETIQ") 2>/dev/null || true
