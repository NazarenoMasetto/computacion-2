#!/usr/bin/env bash
# Ejercicio 1 - Volúmenes. Correr desde ej1_volumes/:  bash comandos.sh
set -u
cd "$(dirname "$0")"

echo "== 1.1 Bind mount: 3 ejecuciones con datos/ montado en /datos =="
for i in 1 2 3; do
    docker run --rm -v "$(pwd)":/app -v "$(pwd)/datos":/datos -w /app python python contador.py
done
echo "Contenido de datos/contador.txt visto desde el host: $(cat datos/contador.txt)"

echo "== 1.1 (pregunta 2) Sin el segundo -v: siempre arranca de 0 =="
for i in 1 2; do
    docker run --rm -v "$(pwd)":/app -w /app python python contador.py
done

echo "== 1.2 Named volume =="
docker volume create contador-data
for i in 1 2 3; do
    docker run --rm -v "$(pwd)":/app -v contador-data:/datos -w /app python python contador.py
done
docker volume inspect contador-data
# El archivo vive en el "Mountpoint" que muestra inspect (zona de Docker, ej.
# /var/lib/docker/volumes/contador-data/_data), solo accesible como root.
# Para leerlo sin tocar ese directorio, lo leemos con otro contenedor:
docker run --rm -v contador-data:/datos python cat /datos/contador.txt; echo

# Limpieza: borrar el volumen que creamos (descomentá si querés)
# docker volume rm contador-data
