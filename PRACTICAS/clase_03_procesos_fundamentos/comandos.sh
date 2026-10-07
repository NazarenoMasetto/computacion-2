#!/usr/bin/env bash
# Clase 3 - Procesos: comandos de terminal de los ejercicios 2, 3 y 4.
# Uso (desde esta carpeta):  bash comandos.sh
# Nota: dentro de un script, $$ es el PID del bash que corre el script.
# Para ver TU shell interactiva, copiá los comandos y pegalos en la terminal.
set -u
cd "$(dirname "$0")"

echo "########## Ejercicio 2: árbol de procesos ##########"
pstree -p $$                          # esta shell y sus descendientes
ps -ef --forest | head -40            # todo el sistema en árbol (recortado)
ps -o pid,ppid,comm -p $$ $(pgrep -P $$)
echo "--- PID 1 ---"
ps -o pid,ppid,user,comm,args -p 1
echo "--- Padre de esta shell ---"
ps -o pid,ppid,comm -p "$(ps -o ppid= -p $$)"
echo "--- Subiendo hasta init (con /proc) ---"
pid=$$
while [ "$pid" -ne 0 ]; do
    ps -o pid=,ppid=,comm= -p "$pid"
    pid=$(ps -o ppid= -p "$pid" | tr -d ' ')
done
# Versión en Python, más detallada:
python3 ej2_jerarquia.py $$

echo "########## Ejercicio 3: memoria virtual ##########"
python3 -c "import time; time.sleep(60)" &
PID_PY=$!
sleep 0.5
cat /proc/$PID_PY/maps
echo "--- text (r-xp del ejecutable) ---"
grep 'r-xp' /proc/$PID_PY/maps | grep -v '\.so' | grep -v '\[' 
echo "--- heap ---";  grep '\[heap\]'  /proc/$PID_PY/maps
echo "--- stack ---"; grep '\[stack\]' /proc/$PID_PY/maps
echo "--- librerías .so cargadas ---"
awk '$6 ~ /\.so/ {print $6}' /proc/$PID_PY/maps | sort -u
kill $PID_PY      # matamos solo el proceso que lanzamos nosotros
# Clasificación automática:
python3 ej3_mapa_memoria.py

echo "########## Ejercicio 4: PIDs y reciclado ##########"
for i in $(seq 1 20); do
    sh -c 'echo "PID=$$"'
done
cat /proc/sys/kernel/pid_max
