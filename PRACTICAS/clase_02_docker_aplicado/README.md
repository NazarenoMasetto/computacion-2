# Clase 2 — Docker Aplicado

Cada ejercicio está en su subcarpeta. Los comandos se corren **desde la subcarpeta indicada**.
Se usa `docker compose` (sin guión, el comando actual); `docker-compose` hace lo mismo.

| Ejercicio | Carpeta / archivo(s) | Cómo correrlo |
|---|---|---|
| 1.1 Bind mount | `ej1_volumes/contador.py`, `ej1_volumes/datos/` | `cd ej1_volumes && docker run --rm -v $(pwd):/app -v $(pwd)/datos:/datos -w /app python python contador.py` |
| 1.2 Named volume | `ej1_volumes/comandos.sh` | `cd ej1_volumes && docker volume create contador-data && docker run --rm -v $(pwd):/app -v contador-data:/datos -w /app python python contador.py` |
| 1 completo | `ej1_volumes/comandos.sh` | `cd ej1_volumes && bash comandos.sh` |
| 2.1 Redes + tarea (servir mi directorio) | `ej2_redes/comandos.sh`, `ej2_redes/publico/index.html` | `cd ej2_redes && bash comandos.sh` |
| 2.2 Redis | `ej2_redes/redis_prueba.py`, `ej2_redes/redis_leer.py` | incluido en `bash comandos.sh` (o a mano con `docker run -it --rm --network redis-net python bash`) |
| 3.1 / 3.2 / 3.3 Dockerfile | `ej3_mi_imagen/{Dockerfile,requirements.txt,app.py,comandos.sh}` | `cd ej3_mi_imagen && docker build -t mi-cowsay . && docker run --rm mi-cowsay` · todo: `bash comandos.sh` |
| 4.1 Compose app + Redis | `ej4_compose_app/docker-compose.yml` (+ `Dockerfile`, `app.py`, `requirements.txt`) | `cd ej4_compose_app && docker compose up` |
| 4.2 Persistencia | `ej4_compose_app/docker-compose.persistencia.yml` | `cd ej4_compose_app && docker compose -f docker-compose.persistencia.yml up` |
| 4.3 Hot reload | `ej4_compose_app/docker-compose.dev.yml` | `cd ej4_compose_app && docker compose -f docker-compose.dev.yml up` (tras editar: `... restart app`) |
| 4 completo | `ej4_compose_app/comandos.sh` | `cd ej4_compose_app && bash comandos.sh` |
| 5 Proyecto integrador | `ej5_proyecto/docker-compose.yml`, `web/{Dockerfile,requirements.txt,server.py}`, `worker/{Dockerfile,requirements.txt,worker.py}` | `cd ej5_proyecto && docker compose up --build` y `curl http://localhost:8000/` (otro puerto: `WEB_PORT=8080 docker compose up`) · todo: `bash comandos.sh` |

Notas:
- En el 4.x guardé las tres variantes del compose en archivos distintos (4.1, 4.2 y 4.3) para no pisar una con otra.
  Saqué la línea `version: '3.8'` (quedó comentada): en Compose v2 es obsoleta y solo genera un warning.
- En el 3.3 `comandos.sh` hace las modificaciones (cambiar el mensaje default y agregar un paquete a `requirements.txt`)
  sobre una **copia temporal**, así los archivos de la entrega quedan como en la consigna.
- Proyecto integrador: `worker` incrementa `contador` en Redis cada `INTERVALO` s (default 1) y guarda la hora del
  último tick; `web` (stdlib `http.server`) responde en `/` un JSON con info del sistema (hostname, Python, kernel, CPUs),
  el contador del worker y cuántas visitas tuvo la web; `/health` devuelve `{"ok": true}`. El worker reintenta la
  conexión hasta que Redis esté listo (`depends_on` solo ordena el arranque, no espera a que Redis acepte conexiones)
  y maneja SIGTERM para que `docker compose down` sea rápido. Redis usa un named volume para no perder el contador.

## Respuestas

**1.1.1 ¿El contador incrementa entre ejecuciones? ¿Por qué?**
Sí: 1, 2, 3... Cada `docker run` es un contenedor nuevo, pero `/datos` es un bind mount de `./datos` del host,
así que el archivo `contador.txt` vive en el host y sobrevive al contenedor.

**1.1.2 ¿Qué pasa si quitás el segundo `-v`?**
Siempre imprime `Contador: 1`. `/datos` queda dentro de la capa escribible del contenedor (el primer `-v` monta
`/app`, no `/datos`), y esa capa se pierde con el contenedor.

**1.1.3 `datos/contador.txt` desde el host:** contiene solo el número (ej. `3`). Queda con dueño root.

**1.2 ¿Podés ver `contador.txt` directamente desde el host? ¿Por qué?**
No de forma directa: un named volume lo administra Docker y vive en su directorio interno
(`docker volume inspect` muestra el `Mountpoint`, ej. `/var/lib/docker/volumes/contador-data/_data`), que solo root
puede leer (y en Docker Desktop está dentro de la VM, ni siquiera en tu filesystem). La forma "limpia" de verlo es
montar el volumen en otro contenedor: `docker run --rm -v contador-data:/datos python cat /datos/contador.txt`.

**2.1 Tarea (servir un directorio propio):**
`docker run -d --name servidor --network ejercicio-red -v $(pwd)/publico:/srv:ro python:3.11 python -m http.server 8000 --directory /srv`.
El otro contenedor llega por nombre (`http://servidor:8000`) gracias al DNS interno de la red creada por el usuario.

**2.2 ¿Los datos persisten en Redis al salir y volver a entrar al contenedor Python? ¿Por qué?**
Sí. Los datos no están en el contenedor de Python sino en la memoria del contenedor `redis`, que sigue corriendo.
El contenedor Python es solo un cliente: lo podés borrar y crear de nuevo y los datos siguen ahí. Se perderían
si se borra/recrea el contenedor de Redis (sin volumen).

**3.1 Ojo con `docker run mi-cowsay "Docker es genial"`:** con `CMD ["python", "app.py"]`, lo que se pone después
de la imagen **reemplaza** el CMD, así que Docker intenta ejecutar un programa llamado `Docker es genial` y falla
(`executable file not found`). Formas de pasar el mensaje: `docker run mi-cowsay python app.py "Docker es genial"`, o
cambiar el Dockerfile a `ENTRYPOINT ["python", "app.py"]` (+ `CMD ["Hola Docker!"]` opcional), donde los argumentos se agregan.

**3.2 ¿Cuánto agregó el Dockerfile sobre la imagen base?**
Poco: lo que muestra `docker history` en las capas propias: `RUN pip install` ≈ 4 MB (cowsay + metadatos),
`COPY requirements.txt`/`COPY app.py` unos pocos KB y `WORKDIR`/`CMD` ~0. La diferencia entre `docker images mi-cowsay`
y `docker images python:3.11-slim` es de unos ~4-5 MB; el resto (~130-150 MB) es la imagen base, que se comparte y no se duplica.

**3.3 ¿Qué pasos se re-ejecutaron? ¿Por qué?**
- Cambiando solo `app.py`: `WORKDIR`, `COPY requirements.txt` y `RUN pip install` salen `CACHED`; solo se rehace `COPY app.py` (y lo que sigue).
- Cambiando `requirements.txt`: se rehacen `COPY requirements.txt`, `RUN pip install` y `COPY app.py`.
Docker cachea capa por capa: si cambia una instrucción o el contenido de los archivos que copia, se invalida esa capa
**y todas las siguientes**. Por eso se copia `requirements.txt` e instala antes de copiar el código: el código cambia
seguido y las dependencias no, entonces el `pip install` (lo lento) casi siempre sale de caché.

**4.1 Tareas:**
1. `docker compose ps` muestra los dos servicios (`app` y `redis`) en estado `Up`.
2. `docker compose logs redis` muestra solo el arranque de Redis (`Ready to accept connections`).
3. Con Ctrl+C y `up` de nuevo **sigue** contando: Ctrl+C solo *detiene* los contenedores, el de Redis se reusa
   (y al apagarse prolijo Redis guarda un snapshot en `/data`). En cambio, si hacés `docker compose down` se borran
   los contenedores y al volver a levantar **arranca de 1** (el `/data` de la imagen oficial es un volumen anónimo que
   no se reutiliza en el contenedor nuevo). Probado: después de `stop`+`up` siguió (12...), después de `down`+`up` volvió a 1.

**4.2 ¿El contador continúa o reinicia? ¿Por qué?**
Continúa, incluso después de `down`. Redis guarda los datos en `/data` (con `--appendonly yes` escribe cada operación
en el archivo AOF) y `/data` ahora es el named volume `redis-data`, que `down` no borra (solo `down -v` lo borra).
Al crear el contenedor nuevo monta el mismo volumen y Redis recarga los datos.

**4.3 Hot reload:** con `.:/app` el contenedor usa el `app.py` del host en vez del copiado en la imagen, así que no hace falta
rebuild: alcanza con `docker compose -f docker-compose.dev.yml restart app`. (Detalle: el `app.py` de la consigna no maneja
SIGTERM y es PID 1, por eso `stop`/`down` tarda ~10 s hasta que Docker lo mata con SIGKILL.)

## Qué se probó

El daemon de Docker anda, pero **Docker Hub está bloqueado por la red del entorno de prueba**, así que no se pudieron bajar
`python`, `python:3.11-slim` ni `redis:alpine`. Para probar igual se armaron imágenes locales equivalentes (Python 3.11/3.13
y redis-server del host) y se usaron sin modificar los archivos de la entrega (con `--build-context python:3.11-slim=...`
y un override de compose solo para la prueba). Con eso se probó y funcionó:
- Ej. 1: bind mount (1, 2, 3), sin segundo `-v` (siempre 1), named volume + `inspect`.
- Ej. 2: red propia y acceso por nombre, la tarea de servir `publico/`, Redis desde un contenedor y persistencia desde otro.
- Ej. 3: `docker build`, `run`, `history`, caché de capas (cambio en `app.py` vs `requirements.txt`) y el problema del CMD.
- Ej. 4: los tres compose (`ps`, `logs`, stop/up continúa, down/up reinicia, con volumen continúa tras down).
- Ej. 5: los 3 servicios, `curl` a la web (puerto de prueba 23080) mostrando el contador avanzando.
Se limpiaron contenedores, volúmenes, redes e imágenes creadas. No se probó con las imágenes oficiales reales.
