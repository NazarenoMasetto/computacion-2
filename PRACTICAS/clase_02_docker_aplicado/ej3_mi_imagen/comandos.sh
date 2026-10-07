#!/usr/bin/env bash
# Ejercicio 3 - Dockerfile. Correr desde ej3_mi_imagen/:  bash comandos.sh
set -u
cd "$(dirname "$0")"

echo "== 3.1 Build y run =="
docker build -t mi-cowsay .
# OJO: con CMD ["python","app.py"], lo que va después del nombre de la imagen
# REEMPLAZA al CMD. Por eso "docker run mi-cowsay 'Docker es genial'" intenta
# ejecutar un programa llamado "Docker es genial" y falla. Para pasarle el
# mensaje hay que repetir el comando (o usar ENTRYPOINT, ver README):
docker run --rm mi-cowsay
docker run --rm mi-cowsay python app.py "Docker es genial"

echo "== 3.2 Inspeccionar la imagen =="
docker history mi-cowsay
docker images mi-cowsay
docker images python:3.11-slim

echo "== 3.3 Optimización: caché de capas =="
# Para no ensuciar los archivos de la entrega, trabajamos sobre una copia.
TMP=$(mktemp -d)
cp Dockerfile requirements.txt app.py "$TMP"/

# a) Cambiar solo app.py -> se reusa la caché del pip install
sed -i 's/Hola Docker!/Hola de nuevo, Docker!/' "$TMP/app.py"
docker build -t mi-cowsay "$TMP"     # mirar los "CACHED" en la salida
docker run --rm mi-cowsay

# b) Cambiar requirements.txt -> se re-ejecuta el pip install y todo lo de abajo
echo "requests==2.32.3" >> "$TMP/requirements.txt"
docker build -t mi-cowsay "$TMP"

rm -rf "$TMP"
# Limpieza (descomentá si querés borrar la imagen):
# docker rmi mi-cowsay
