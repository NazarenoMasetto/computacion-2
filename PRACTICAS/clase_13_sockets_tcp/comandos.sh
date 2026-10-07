#!/usr/bin/env bash
# Clase 13 - comandos de terminal para los ejercicios 1, 5 y 6.
# No se ejecuta "de corrido": son bloques para copiar en dos/tres terminales.
# Nada de esto necesita root ni modifica el sistema.

PUERTO=${PUERTO:-8080}

# Función auxiliar: muestra las conexiones TCP de un puerto.
# Usa `ss` si está; si no (contenedores mínimos), lee /proc/net/tcp.
# En /proc: st 0A=LISTEN 01=ESTAB 02=SYN_SENT 06=TIME_WAIT; tx:rx en hexa.
conexiones() {
    local p=${1:-$PUERTO}
    if command -v ss >/dev/null; then
        ss -tan "( sport = :$p or dport = :$p )"
    else
        local h; h=$(printf ':%04X' "$p")
        awk -v h="$h" 'NR>1 && (substr($2,length($2)-4)==h || substr($3,length($3)-4)==h) {print $2, $3, "st="$4, "tx:rx="$5}' /proc/net/tcp
    fi
}

ej1_1() {
    # Terminal 1: nc de servidor
    nc -l "$PUERTO"
    # Terminal 2: python3 ej1_cliente_nc.py --port $PUERTO
    #             python3 ej1_cliente_nc.py --port $PUERTO --sin-recv   (punto 3)
}

ej1_2() {
    # Terminal 1: python3 ej1_servidor_nc.py --port $PUERTO
    # Terminal 2:
    echo "hola server" | nc -q1 localhost "$PUERTO"
}

ej1_3() {
    # 6. servidor SIN SO_REUSEADDR; conectarse con nc y matar el SERVIDOR
    #    (así el que cierra primero es el server y el TIME_WAIT queda de su lado)
    #    Terminal 1: python3 ej1_servidor_nc.py --port $PUERTO --sin-reuse
    #    Terminal 2: nc localhost $PUERTO        (no escribir nada)
    #    Terminal 1: Ctrl+C, cortar el nc y relanzar -> "Address already in use"
    # 7. ver el TIME_WAIT:
    if command -v ss >/dev/null; then
        ss -tan state time-wait | head
    else
        conexiones "$PUERTO" | grep 'st=06'
    fi
}

ej5_3() {
    # 7. con servidor_eco.py corriendo: conectarse y matar nc con Ctrl+C
    nc localhost "$PUERTO"
}

ej6() {
    # Terminal 1: python3 servidor_eco.py --port $PUERTO --lento 10
    #             (punto 5: agregar --backlog 1)
    # Terminales 2, 3, 4, 5: nc localhost $PUERTO
    # Otra terminal, mientras el primero está siendo atendido:
    conexiones "$PUERTO"
}

# Uso: bash comandos.sh ej6   (o cualquier otra función de arriba)
if [[ $# -gt 0 ]]; then
    "$@"
fi
