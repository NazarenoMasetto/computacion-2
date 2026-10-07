# Clase 1 — Docker Intro

Todos los comandos se corren **desde esta carpeta**.

| Ejercicio | Archivo(s) | Cómo correrlo |
|---|---|---|
| 1.1 / 1.2 / 1.3 — Explorar contenedores | `comandos.sh` (sección Ej. 1) | `docker run -it ubuntu bash` (interactivo) o `bash comandos.sh` (versión no interactiva) |
| 2.1 / 2.2 / 2.3 — Python en Docker | `comandos.sh` (sección Ej. 2) | `docker run -it python` · `docker run python:3.11 python --version` |
| 3.1 / 3.2 — Script local en Docker | `hola.py` | `docker run --rm -v $(pwd):/app -w /app python python hola.py` |
| 3.3 — Entender el montaje | `comandos.sh` (sección Ej. 3.3) → genera `desde_docker.txt` | ver `comandos.sh` y después `cat desde_docker.txt` |
| 4.1 / 4.2 — Gestión de contenedores | `comandos.sh` (sección Ej. 4) | `docker run -d --name mi-python python sleep 300` ... `docker stop mi-python && docker rm mi-python` |
| 5.1 / 5.2 — Script con dependencias | `con_dependencias.py` | `docker run --rm -v $(pwd):/app -w /app python sh -c "pip install requests && python con_dependencias.py"` |
| Síntesis | `info_sistema.py` | Local: `python3 info_sistema.py` · `docker run --rm -v $(pwd):/app -w /app python:3.11 python info_sistema.py` · ídem con `python:3.9` |
| Todo junto | `comandos.sh` | `bash comandos.sh` |

`comandos.sh` etiqueta cada contenedor que crea con `curso=c2-clase01` y al final borra **solo esos**.
En vez de `docker container prune` a secas (que borra todos los contenedores detenidos del usuario) usa
`docker container prune -f --filter label=curso=c2-clase01`.

## Respuestas

**1.1 — ¿Qué se ve adentro del Ubuntu?**
`/etc/os-release` muestra la versión de Ubuntu de la imagen (la `latest`, hoy una LTS). `whoami` da `root`.
`ps aux` muestra poquísimos procesos: `bash` con **PID 1** y el propio `ps`; el contenedor tiene su propio
espacio de PIDs y no ve los procesos del host. `ls /` muestra un árbol Linux normal pero es el filesystem de la imagen.

**1.2 — ¿Cómo hacer que cowsay esté siempre disponible?**
Cada `docker run` crea un contenedor nuevo desde la imagen original, así que lo instalado se pierde.
La solución es crear una imagen propia con un `Dockerfile` (`FROM ubuntu` + `RUN apt-get update && apt-get install -y cowsay`)
y hacer `docker build`. (También existe `docker commit` sobre el contenedor modificado, pero no es reproducible.)

**1.3 — ¿Cuántos contenedores tenés?**
Uno por cada `docker run` que hiciste: `docker ps` muestra solo los que están corriendo, `docker ps -a` muestra
también los detenidos (quedan ahí hasta que los borrás o usás `--rm`).

**2.3 — ¿La versión local es la misma que la del contenedor por defecto?**
En general no. La imagen `python` (tag `latest`) trae la última versión estable de CPython; la local depende
de la distro (en la máquina de prueba: Python 3.13). Por eso conviene fijar el tag (`python:3.11`) y no depender de `latest`.

**3.2 — Qué se nota al correr `hola.py`:**
el hostname es el ID corto del contenedor, el directorio es `/app`, se listan los archivos de la carpeta local
(por el bind mount) y `USER` sale `desconocido` porque la imagen no define esa variable.

**3.3 — Montaje:** el archivo `desde_docker.txt` aparece en el host porque `-v $(pwd):/app` comparte el mismo
directorio. Detalle: queda con dueño `root`, porque el proceso del contenedor corre como root.

**5.2 — ¿Por qué la "solución temporal" no es buena?**
Porque baja e instala `requests` en **cada** ejecución (lento, necesita red) y la versión instalada puede cambiar
entre corridas: no es reproducible. Lo correcto es una imagen con las dependencias ya instaladas (clase 2).

**Síntesis — Diferencias entre local, python:3.11 y python:3.9:**
- **Versión de Python**: cambia según el tag (3.13 local, 3.11.x y 3.9.x en los contenedores).
- **Kernel**: es el **mismo** en los tres (`platform.release()` da lo mismo): los contenedores comparten el kernel del host.
- **Distribución**: local es la del host (Ubuntu); las imágenes oficiales `python` son Debian.
- **Hostname**: en Docker es el ID del contenedor.
- **CPUs y memoria**: por defecto son las mismas que el host (`/proc/meminfo` muestra la memoria del equipo).
  Solo cambian si se limitan con `--cpus` / `-m`; el script muestra el límite real leyendo el cgroup
  (probado: con `-m 256m` muestra `256 MB`).
- **Variables `PYTHON*`**: las imágenes oficiales definen `PYTHON_VERSION` (y otras como `PYTHON_SHA256`);
  en local normalmente no hay ninguna, salvo que uno las haya seteado.

## Qué se probó

- `info_sistema.py`, `hola.py` localmente (Python 3.13): OK.
- El daemon de Docker anda, pero **Docker Hub está bloqueado por la red del entorno de prueba** (no se pueden
  bajar `ubuntu`, `python`, `hello-world`). Para probar igual se armaron imágenes locales mínimas con el Python
  del host (3.11 y 3.13) y con ellas se corrieron: bind mount de `hola.py`, creación de `desde_docker.txt`,
  contenedor en background + `docker exec` + `stop`/`rm`, la falla de `con_dependencias.py` sin `requests`,
  e `info_sistema.py` en 3.11 y 3.13 (y con `-m 256m`). Todo OK.
- No se pudo probar: los pasos con la imagen `ubuntu` (cowsay), `python:3.9`/`3.8-slim`, ni `con_dependencias.py`
  completo (httpbin.org también está bloqueado). `comandos.sh` se validó con `bash -n`.
