#!/usr/bin/env bash
# Clase 14 - comandos para medir y observar los servidores.
# Uso: bash comandos.sh <funcion> [args]     (ej: bash comandos.sh medir_todos)
# Todo corre como usuario normal; los servidores se lanzan con `timeout`
# para que nunca queden colgados.

PUERTO=${PUERTO:-8080}

# Ej 1.1/1.2: las cuatro estrategias con --lento (default 1) y N clientes (default 20)
medir_todos() {
    local lento=${1:-1} clientes=${2:-20}
    for modo in secuencial threads fork pool; do
        timeout 120 python3 servidores_eco.py --modo "$modo" --port "$PUERTO" --lento "$lento" >/dev/null &
        local sp=$!; sleep 0.5
        echo "=== $modo (lento=$lento, clientes=$clientes)"
        timeout 100 python3 benchmark.py --port "$PUERTO" --clientes "$clientes"
        kill "$sp"; wait "$sp" 2>/dev/null
    done
}

# Ej 1.3: escala (modo threads o fork)
escala() {
    local modo=${1:-threads}
    timeout 300 python3 servidores_eco.py --modo "$modo" --port "$PUERTO" --lento 1 >/dev/null &
    local sp=$!; sleep 0.5
    for n in 50 100 200 500 1000; do
        echo "=== $modo con $n clientes"
        timeout 60 python3 benchmark.py --port "$PUERTO" --clientes "$n" | grep -E 'Compl|total|máx|Fall|  '
    done
    kill "$sp"; wait "$sp" 2>/dev/null
    echo "ulimit -n = $(ulimit -n)"
}

# Ej 2: pool saturado (workers default 5)
pool() {
    local w=${1:-5}
    timeout 120 python3 servidores_eco.py --modo pool --workers "$w" --port "$PUERTO" --lento 1 >/dev/null &
    local sp=$!; sleep 0.5
    timeout 100 python3 benchmark.py --port "$PUERTO" --clientes 20
    kill "$sp"; wait "$sp" 2>/dev/null
}

# Ej 3: contar descriptores y zombies del PADRE de ej3_server_fork_descuidos.py
#   Terminal 1: python3 ej3_server_fork_descuidos.py --descuido guardar   (imprime el pid)
#   Terminal 2: bash comandos.sh observar_fork <PID_PADRE>
observar_fork() {
    local pp=$1
    echo "fds del padre antes:  $(ls /proc/"$pp"/fd | wc -l)"
    for _ in 1 2; do python3 benchmark.py --port "$PUERTO" --clientes 50 >/dev/null; done
    sleep 0.5
    echo "fds del padre después: $(ls /proc/"$pp"/fd | wc -l)"
    echo "hijos (STAT Z = zombie):"
    ps --ppid "$pp" -o pid,stat,comm | head -5
    echo "zombies: $(ps --ppid "$pp" -o stat= | grep -c '^Z')"
}

# Ej 3 A2 punto 7: matar al primer hijo del padre (con un cliente conectado)
#   Terminal 2: python3 ej3_cliente_espera.py
#   Terminal 3: bash comandos.sh matar_hijo <PID_PADRE>
matar_hijo() {
    local hijo; hijo=$(ps --ppid "$1" -o pid= | head -1)
    echo "matando hijo $hijo"; kill "$hijo"
}

# Ej 4: race condition (repetir varias veces)
#   Terminal 1: python3 ej4_threads_race.py --sin-lock --pausa 0.0001
#   Terminal 2: bash comandos.sh carga 200  -> después Ctrl+C en la terminal 1
carga() {
    for _ in 1 2 3; do python3 benchmark.py --port "$PUERTO" --clientes "${1:-200}" | grep Compl; done
}

# Ej 6: núcleos y GIL
info_cpu() {
    nproc
    python3 -c "import sys; print('con GIL' if sys._is_gil_enabled() else 'SIN GIL')"
}

if [[ $# -gt 0 ]]; then
    "$@"
fi
