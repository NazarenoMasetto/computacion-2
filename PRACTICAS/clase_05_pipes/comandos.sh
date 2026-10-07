#!/usr/bin/env bash
# Clase 5 — comandos de terminal de los ejercicios 1.1, 2.2, 6.1, 7 y adicionales.
# Todo lo que se crea va a un directorio temporal que se borra al final.
# Uso: bash comandos.sh   (desde cualquier lado)

set -u
AQUI="$(cd "$(dirname "$0")" && pwd)"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
cd "$TMP" || exit 1

echo "===== Ej 1.1: file descriptors del shell ====="
# $$ es el PID del shell que corre este script
ls -la /proc/$$/fd

echo "--- abrimos /etc/passwd como fd 3 ---"
exec 3< /etc/passwd
ls -la /proc/$$/fd           # ahora aparece 3 -> /etc/passwd
read -r linea <&3            # leemos una línea desde el fd 3
echo "Leí: $linea"
exec 3<&-                    # cerramos el fd 3
echo "--- fd 3 cerrado ---"
ls -la /proc/$$/fd

echo
echo "===== Ej 2.2: stdout vs stderr ====="
echo "--- > solo_stdout.txt (stderr sigue saliendo por pantalla) ---"
python3 "$AQUI/separar_salidas.py" > solo_stdout.txt
echo "contenido de solo_stdout.txt:"; cat solo_stdout.txt

echo "--- 2> solo_stderr.txt (stdout sale por pantalla) ---"
python3 "$AQUI/separar_salidas.py" 2> solo_stderr.txt
echo "contenido de solo_stderr.txt:"; cat solo_stderr.txt

echo "--- > stdout.txt 2> stderr.txt (nada por pantalla) ---"
python3 "$AQUI/separar_salidas.py" > stdout.txt 2> stderr.txt
echo "stdout.txt:"; cat stdout.txt
echo "stderr.txt:"; cat stderr.txt

echo "--- > todo.txt 2>&1 (ambos al mismo archivo) ---"
python3 "$AQUI/separar_salidas.py" > todo.txt 2>&1
echo "todo.txt:"; cat todo.txt

echo
echo "===== Ej 6.1: filtro mayusculas.py ====="
echo "hola mundo" | python3 "$AQUI/mayusculas.py"
seq 1 20 | sed 's/^/linea /' > archivo.txt
cat archivo.txt | python3 "$AQUI/mayusculas.py" | head -5

echo
echo "===== Ej 7: named pipe (escritor en background, lector en primer plano) ====="
FIFO="$TMP/mi_canal"
python3 "$AQUI/escritor_fifo.py" 3 0.3 "$FIFO" > escritor.log &
sleep 0.3                    # damos tiempo a que el escritor cree la FIFO
python3 "$AQUI/lector_fifo.py" "$FIFO"
wait
echo "log del escritor:"; cat escritor.log
ls -l "$FIFO"                # la 'p' al principio indica que es un pipe con nombre

echo
echo "===== Adicional: tee casero ====="
ls -la /etc | head -5 | python3 "$AQUI/mi_tee.py" salida.txt
echo "salida.txt tiene $(wc -l < salida.txt) líneas"

echo
echo "===== Adicional: monitor de pipe ====="
seq 1 50000 > grande.txt
cat grande.txt | python3 "$AQUI/monitor.py" 20000 | wc -l
