# Bloque 0 - Filesystem de Linux

Todo en Python 3.10+ y solo stdlib. Los scripts manejan rutas absolutas y relativas,
archivos inexistentes, falta de permisos y symlinks rotos sin explotar.
Los que borran o modifican cosas (`broken_links.py --delete`, `sync.py`, `fixperms.py`,
`dedup.py --delete`) **siempre piden confirmación** (o tienen `--dry-run`).

| Ejercicio | Archivo(s) | Cómo correrlo |
|-----------|-----------|---------------|
| 1.1 Investigando el sistema | `comandos.sh`, `ejercicio_1_1_respuestas.txt` | `bash comandos.sh` |
| 1.2 Permisos | `comandos.sh` (sección 1.2) | `bash comandos.sh` (trabaja en un dir de `mktemp -d` y lo borra) |
| 1.3 Enlaces duros vs simbólicos | `comandos.sh` (sección 1.3) | `bash comandos.sh` |
| **2.1 Inspector (OBLIGATORIO)** | `inspector.py` | `python3 inspector.py /etc/passwd /dev/null /bin /home` |
| 2.2 Archivos grandes | `find_large.py` | `python3 find_large.py /var/log --min-size 1M` · `python3 find_large.py . --min-size 100K --type f` · `python3 find_large.py /home --min-size 50M --top 10` |
| 2.3 Enlaces rotos | `broken_links.py` | `python3 broken_links.py ~` · `python3 broken_links.py ~ --delete` · `python3 broken_links.py /etc --quiet` |
| 3.1 Comparador de directorios | `diffdir.py` | `python3 diffdir.py dir1 dir2` · `... --recursive` · `... --checksum` |
| 3.2 Uso de disco | `diskusage.py` | `python3 diskusage.py ~ --depth 1` · `python3 diskusage.py . --top 5` · `python3 diskusage.py . --depth 2 --exclude "node_modules,*.log"` (`--no-human` para bytes) |
| 3.3 Sincronizador | `sync.py` | `python3 sync.py origen/ destino/` · `... --dry-run` · `... --delete` · `... --exclude "*.tmp"` (`-y` para no preguntar) |
| 4.1 Monitor de cambios | `watch.py` | `python3 watch.py /var/log` (`--interval 0.5`, `-r` recursivo; Ctrl+C para salir) |
| 4.2 Normalizador de permisos | `fixperms.py` | `python3 fixperms.py proyecto/ --files 644 --dirs 755 --scripts 755` (`--dry-run`, `-y`, `-v`) |
| 4.3 Deduplicador | `dedup.py` | `python3 dedup.py ~/Downloads` · `python3 dedup.py ~/Downloads --delete` |

Notas de diseño:
- `inspector.py`: usa `os.lstat` (para ver el symlink y no su destino). Linux no expone la
  fecha de creación vía `os.stat` (no hay `st_birthtime`), así que se aclara y se muestra ctime.
  Para dispositivos muestra major/minor en lugar de tamaño.
- `find_large.py`: `--min-size` acepta `500`, `100K`, `1M`, `2G` (también `1MB`), base 1024.
  Con `--type d` el tamaño de un directorio es la suma de lo que contiene.
- `diffdir.py`: sin `--checksum` compara tamaño y fecha; con `--checksum`, a igual tamaño compara SHA-256.
  Si falta una carpeta entera se informa la carpeta (no cada archivo adentro).
- `sync.py`: un archivo está "modificado" si cambia tamaño o mtime (como rsync por defecto).
  Como copia con `shutil.copy2`, la segunda corrida ya no detecta cambios. Sin `--delete`
  los sobrantes se informan pero no se tocan.
- `watch.py`: hace *polling* (stdlib); detecta renombres porque el inodo se conserva.
- `dedup.py`: agrupa por tamaño primero y solo hashea los que coinciden; los enlaces duros
  no se cuentan como copias (mismo inodo = mismo archivo).

## Qué se probó

Todo se corrió con `timeout` en Linux / Python 3.13 sobre directorios de prueba temporales:
- `comandos.sh` completo (salida real usada para las respuestas de 1.1).
- `inspector.py` con `/etc/passwd`, `/dev/null`, `/bin`, `/home`, un symlink roto y una ruta inexistente.
- `find_large.py` con `--min-size`, `--type f/d`, `--top`, tamaño inválido y directorio inexistente.
- `broken_links.py` normal, `--quiet` y `--delete` (confirmando solo uno: borró solo ese, el symlink válido quedó).
- `diffdir.py` con archivos solo-en-uno, carpetas faltantes, distinto tamaño, distinta fecha y `-r --checksum`.
- `diskusage.py` con `--depth`, `--top`, `--exclude`, `--no-human`.
- `sync.py` con `--dry-run`, cancelación, `--delete` + `--exclude`, y re-ejecución (sin cambios). Verificado luego con `diffdir.py`.
- `watch.py` detectando MODIFICADO, CREADO, ELIMINADO y RENOMBRADO.
- `fixperms.py` con `--dry-run`, aplicación real y permiso inválido.
- `dedup.py` con grupos de 3 y 2 copias, enlace duro ignorado, y `--delete`.

No se pudo probar el caso "sin permisos" (directorio sin `x`, archivos ilegibles) porque el
entorno de prueba corre como root, y root ignora los permisos. El código igual los maneja
(captura `PermissionError`/`OSError`).

## Respuestas

### 1.1 Investigando el sistema
Ver `ejercicio_1_1_respuestas.txt` (con comandos y valores obtenidos). Resumen:
1. `find /etc -maxdepth 1 -type f | wc -l` → 76 archivos regulares (167 entradas en total con `ls -A /etc | wc -l`).
2. `stat -c %s /etc/passwd` → 3333 bytes.
3. `/dev/null` es un **dispositivo de caracteres** (`c` en `ls -l`, major 1 minor 3). Todo lo que se escribe se descarta y leerlo da EOF al toque; sirve para tirar salida o como entrada vacía.
4. `readlink /bin` → `usr/bin` (usrmerge).
5. `ls -i ~/.bashrc` → 175682 (depende de la máquina).
6. `/home` tiene 4 enlaces: su nombre en `/`, su propio `.`, y el `..` de cada uno de sus 2 subdirectorios. En general: 2 + cantidad de subdirectorios.

### 1.2 Permisos
- **Error al ejecutar:** `Permission denied`. El archivo se crea con `rw-r--r--` (umask 022) y no tiene bit `x`, así que el kernel no deja ejecutarlo. (Con `bash mi_script.sh` sí anda, porque ahí se ejecuta bash y el script solo se lee.)
- **`-rw-r--r--`:** el primer carácter es el tipo (`-` archivo regular, `d` dir, `l` link). Después tres grupos de `rwx`: dueño (`rw-`: lee y escribe), grupo (`r--`: solo lee), otros (`r--`: solo lee).
- **`chmod +x` vs `chmod 755`:** `+x` es *relativo*: agrega la `x` a lo que ya había (respetando umask) sin tocar el resto. `755` es *absoluto*: deja exactamente `rwxr-xr-x` sin importar lo anterior. Ejemplo probado: un archivo `600` con `+x` queda `711`; con `755` queda `755`.
- **Permisos 644:** pueden leerlo todos (dueño, grupo y otros); solo el dueño puede escribirlo (y root, que ignora permisos).
- **`x` en directorios:** en un directorio, `r` permite listar los nombres y `x` permite *atravesarlo*: entrar con `cd`, acceder a archivos adentro y ver su metadata (resolver un path pasa por cada directorio). Sin `x` no podés abrir `dir/archivo` aunque sepas el nombre.

### 1.3 Enlaces duros vs simbólicos
- **Observación con `ls -li`:** `original.txt` y `enlace_duro.txt` tienen el mismo inodo y contador de enlaces 2: son dos nombres para el mismo archivo. `enlace_simbolico.txt` tiene otro inodo, tipo `l` y tamaño 12 (el largo del texto "original.txt").
- **Al borrar el original:** `rm` solo borra un nombre y baja el contador a 1; los datos siguen porque el enlace duro todavía apunta al inodo, entonces `cat enlace_duro.txt` funciona. El simbólico guarda un *nombre* que ya no existe → `No such file or directory` (link roto, se ve en rojo).
- **Cuándo usar cada uno:** simbólicos para atajos, apuntar a directorios, cruzar filesystems o versiones intercambiables (`python -> python3.13`, configs en `/etc/alternatives`). Duros cuando querés que el contenido sobreviva aunque se borre un nombre, por ejemplo backups incrementales tipo snapshots (rsync `--link-dest`) sin duplicar espacio; pero solo sirven dentro del mismo filesystem y no para directorios.
