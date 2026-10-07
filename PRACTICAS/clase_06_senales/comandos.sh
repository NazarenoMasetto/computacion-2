#!/usr/bin/env bash
# Ejercicio 1 - Explorando señales desde la terminal (1.1, 1.2 y 1.3).
# Seguro: solo manda señales a procesos que lanza este mismo script ($!).
# Uso: bash comandos.sh

set -u

echo "=================== 1.1 Listando señales del sistema ==================="
kill -l
echo
# man 7 signal puede no estar instalado (ej: en contenedores mínimos)
EXTRACTO=$(man 7 signal 2>/dev/null | grep -A 40 "Standard signals" | head -45)
if [ -n "$EXTRACTO" ]; then
    echo "--- Extracto de 'man 7 signal' (tabla de señales estándar) ---"
    echo "$EXTRACTO"
else
    echo "(man 7 signal no disponible en este sistema)"
fi

echo
echo "=================== 1.2 Enviando señales a procesos ==================="
# En vez de dos terminales, lanzamos el sleep en background y guardamos su PID
sleep 1000 &
PID=$!
echo "Lancé 'sleep 1000' con PID $PID"
# pgrep -x sleep mostraría todos los sleep del sistema; filtramos el nuestro
pgrep -x sleep | grep -w "$PID"
ps -o pid,stat,cmd -p "$PID"

echo "--- kill -STOP $PID (pausar) ---"
kill -STOP "$PID"
sleep 0.2
ps -o pid,stat,cmd -p "$PID"     # STAT = T (stopped)

echo "--- kill -CONT $PID (continuar) ---"
kill -CONT "$PID"
sleep 0.2
ps -o pid,stat,cmd -p "$PID"     # STAT = S (sleeping, otra vez vivo)

echo "--- kill $PID (SIGTERM) ---"
kill "$PID"
wait "$PID" 2>/dev/null
echo "Código de salida: $?  (128 + 15 = 143 -> murió por SIGTERM)"

# Caso SIGKILL: un proceso que ignora SIGTERM
echo "--- Proceso que ignora SIGTERM: hace falta kill -9 ---"
python3 -c 'import signal, time; signal.signal(signal.SIGTERM, signal.SIG_IGN); time.sleep(1000)' &
PID2=$!
sleep 0.2
kill "$PID2"
sleep 0.3
if kill -0 "$PID2" 2>/dev/null; then
    echo "Sigue vivo después de SIGTERM (lo ignora). Mando SIGKILL..."
    kill -9 "$PID2"
fi
wait "$PID2" 2>/dev/null
echo "Código de salida: $?  (128 + 9 = 137 -> SIGKILL)"

echo
echo "=================== 1.3 Observando señales con strace ==================="
if command -v strace >/dev/null; then
    TMP=$(mktemp -d)
    # Python sin handler para USR1 -> acción por defecto: terminar
    strace -o "$TMP/strace.txt" -e trace=signal python3 -c "import time; time.sleep(10)" &
    SPID=$!
    sleep 1                       # dar tiempo a que arranque python
    # $! es el PID de strace; la señal hay que mandarla al python (hijo de strace)
    PYPID=$(pgrep -P "$SPID" | head -1)
    echo "strace PID=$SPID, python PID=$PYPID -> kill -USR1 $PYPID"
    kill -USR1 "$PYPID"
    wait "$SPID" 2>/dev/null
    echo "--- Últimas líneas de strace ---"
    tail -n 5 "$TMP/strace.txt"
    rm -rf "$TMP"
else
    echo "strace no está instalado (apt install strace)"
fi
