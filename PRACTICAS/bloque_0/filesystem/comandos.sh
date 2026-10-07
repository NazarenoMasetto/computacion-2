#!/usr/bin/env bash
# Ejercicios 1.1, 1.2 y 1.3 - Filesystem de Linux (exploración desde la terminal).
# Todo lo que crea archivos se hace en un directorio temporal, nunca en el home.
# Uso: bash comandos.sh

set -u

echo "=================== Ejercicio 1.1: Investigando el sistema ==================="

echo "--- 1. Archivos directamente en /etc (sin subdirectorios) ---"
# Solo archivos regulares en el primer nivel:
find /etc -maxdepth 1 -type f | wc -l
# Todas las entradas (archivos, dirs, links), sin . y ..:
ls -A /etc | wc -l

echo "--- 2. Tamaño exacto de /etc/passwd en bytes ---"
stat -c '%s bytes' /etc/passwd
ls -l /etc/passwd

echo "--- 3. Tipo de /dev/null ---"
file /dev/null
ls -l /dev/null          # la 'c' inicial = dispositivo de caracteres

echo "--- 4. A dónde apunta /bin ---"
ls -ld /bin
readlink /bin
readlink -f /bin         # ruta absoluta resuelta

echo "--- 5. Inodo de ~/.bashrc (o ~/.zshrc) ---"
if [ -e ~/.bashrc ]; then ls -i ~/.bashrc; stat -c 'Inodo: %i' ~/.bashrc
elif [ -e ~/.zshrc ]; then ls -i ~/.zshrc; stat -c 'Inodo: %i' ~/.zshrc
else echo "No hay .bashrc ni .zshrc en este usuario"; fi

echo "--- 6. Enlaces duros de /home ---"
stat -c 'Links: %h' /home
ls -la /home             # cada subdirectorio aporta un '..' que apunta a /home

echo
echo "=================== Ejercicio 1.2: Permisos ==================="
TMP=$(mktemp -d)
cd "$TMP" || exit 1
echo "Trabajando en $TMP"

# Paso 1: crear el script
echo 'echo "Hola desde el script"' > mi_script.sh

# Paso 2: intentar ejecutarlo (falla: Permission denied, no tiene bit x)
./mi_script.sh || echo "(falló como se esperaba: no tiene permiso de ejecución)"

# Paso 3: ver permisos actuales (-rw-r--r-- con umask 022)
ls -l mi_script.sh

# Paso 4: agregar ejecución
chmod +x mi_script.sh

# Paso 5: verificar y ejecutar
ls -l mi_script.sh
./mi_script.sh

# Extra: chmod +x vs chmod 755
chmod 600 mi_script.sh; chmod +x mi_script.sh; echo -n "600 + (+x)  -> "; stat -c '%A (%a)' mi_script.sh
chmod 755 mi_script.sh;                        echo -n "chmod 755   -> "; stat -c '%A (%a)' mi_script.sh

# Extra: un directorio sin 'x' no se puede atravesar
mkdir sin_x && echo hola > sin_x/a.txt
chmod 644 sin_x
ls sin_x 2>&1 || true            # puede listar nombres (r) pero sin metadata
cat sin_x/a.txt 2>&1 || true     # no puede entrar (falta x) -> Permission denied
# (si corrés como root, root ignora los permisos y todo funciona)
chmod 755 sin_x

echo
echo "=================== Ejercicio 1.3: Enlaces duros vs simbólicos ==================="
mkdir experimento_enlaces
cd experimento_enlaces || exit 1

echo "Este es el contenido original" > original.txt

# Paso 1: crear ambos enlaces
ln original.txt enlace_duro.txt
ln -s original.txt enlace_simbolico.txt

# Paso 2: inodos (el duro comparte inodo con el original, el simbólico tiene uno propio)
ls -li

# Paso 3: contador de enlaces -> Links: 2
stat original.txt | grep Links

# Paso 4: borrar el original
rm original.txt

# Paso 5: leer cada enlace
echo -n "enlace_duro.txt: "; cat enlace_duro.txt
echo -n "enlace_simbolico.txt: "; cat enlace_simbolico.txt 2>&1 || true

# Paso 6: ver el estado (el simbólico queda colgando)
ls -l

# Limpieza: solo borramos el directorio temporal que creamos nosotros
cd / && rm -rf "$TMP"
echo "Directorio temporal eliminado."
