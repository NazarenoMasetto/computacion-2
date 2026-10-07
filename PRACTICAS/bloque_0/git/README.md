# Bloque 0 — Git y GitHub

## Ejercicios

| Ejercicio | Archivo | Cómo correrlo (desde esta carpeta) |
|---|---|---|
| Parte 1: primer repo, ritmo de trabajo, historia (`log`, `show`, `blame`) | `practica_git.sh` | `bash practica_git.sh` |
| Parte 2: branches, conflictos, `.gitignore` | `practica_git.sh` | (mismo script) |
| Parte 3: subir a un remoto y simular colaboración | `practica_git.sh` | (mismo script) |
| Extra: `stash` y `rebase -i` | `practica_git.sh` | (mismo script) |
| Tu repositorio del curso | este mismo repo | ver sección abajo |

`practica_git.sh` hace toda la práctica en un directorio de `mktemp -d` (lo imprime al
principio y al final, para que puedas entrar y mirar). No toca la configuración global
de git: el usuario se configura solo en los repos temporales, con datos de ejemplo.
Con `BORRAR=1 bash practica_git.sh` el directorio se borra al terminar.

Para poder correrlo sin intervención:
- **GitHub se simula con un repo `--bare` local** (`github-ejercicio-git.git`) que hace de
  `origin`, y la "edición desde la web" se hace desde un segundo clon (`clon-web`).
  Con GitHub real los comandos son los mismos, cambiando la URL del `remote add`.
- El conflicto se resuelve con `sed` (combinando las dos versiones) y el commit de merge
  usa `--no-edit` en vez de abrir el editor.
- El `rebase -i HEAD~3` se hace con `GIT_SEQUENCE_EDITOR=sed ...` (1 `reword` + 2 `squash`).
- En "Simulando colaboración" el cambio local va a `notas.txt` (no al README) para que
  el `pull` mergee sin conflicto, que es el caso que describe la consigna.

## Tu repositorio del curso

Este ejercicio **es este repositorio** (`computacion2-2026`), así que no se recrea en el
script. Lo que pide la consigna y cómo queda:

1. Repo en GitHub `computacion2-2026`, **privado**, sin README inicial.
2. Estructura local: `git init` y `mkdir -p bloque_0/{git,argparse,filesystem,python_avanzado} tp1 tp2`
   (acá además hay otras carpetas de `bloque_0`).
3. `README.md` en la raíz con los datos del estudiante (nombre, legajo, email, usuario de
   GitHub — se completan con los datos reales, acá van placeholders), la estructura y la
   tabla de estado.
4. `.gitignore` con `venv/`, `__pycache__/`, `*.pyc`, `.env`, `.idea/`, `.vscode/`, `.DS_Store`.
5. Primer commit y push:
   ```bash
   git add .
   git commit -m "Estructura inicial del repositorio del curso"
   git remote add origin https://github.com/TU-USUARIO/computacion2-2026.git
   git push -u origin main
   ```
6. En GitHub: *Settings → Collaborators → Add people → `gquintero-um`* (se hace desde la web).

Después, cada ejercicio se agrega con `git add <archivo>`, `git commit -m "mensaje descriptivo"`
y `git push`, con commits chicos y frecuentes.

## Respuestas

**¿Qué ves con `git status` antes de agregar `main.py`?** El archivo aparece en
*Untracked files*: git lo ve en la carpeta pero no lo sigue hasta que lo agregues.

**¿Qué pasaría con un solo commit para los dos cambios de `main.py`?** Funcionaría igual,
pero la historia diría menos: no se podría ver (ni revertir) por separado "agregar el
programa" y "personalizar el saludo". Commits chicos = historia más fácil de leer,
de revisar con `git show`/`git blame` y de deshacer.

**`git diff`:** muestra con `-` (rojo) la línea `print("Hello World")` y con `+` (verde)
la nueva. Sirve para revisar qué vas a commitear.

**`git blame`:** en un repo personal todas las líneas son tuyas, pero muestra en qué commit
entró cada línea; en equipo sirve para saber quién y por qué cambió algo.

**Branches: ¿dónde está la función `suma` al volver a `main`?** No está: los commits de
`feature-suma` no afectan a `main` hasta el merge. Como `main` no había avanzado, el merge
es *fast-forward* (solo mueve el puntero). En cambio el merge de `version-a` sí crea un
commit de merge con dos padres, que se ve en `git log --oneline --graph --all`.

**Conflictos:** aparecen porque las dos ramas cambiaron la misma línea; git marca la zona
con `<<<<<<< HEAD` / `=======` / `>>>>>>> version-a`, uno deja el contenido final, borra los
marcadores, hace `git add` y `git commit`. No es un error, es git pidiendo que decidas.

**`.gitignore`:** después de crearlo, `.env` y `__pycache__/` desaparecen de `git status`.
Detalle observado: con Python 3.13, `python -m venv venv` ya crea un `.gitignore` con `*`
*adentro* de `venv/`, así que el venv ni siquiera aparecía; igual conviene tener `venv/`
en el `.gitignore` del repo. El script también muestra la advertencia de la consigna: un
archivo ya commiteado (`config.local`) sigue apareciendo como modificado aunque esté en
`.gitignore`, hasta que se lo saca del índice con `git rm --cached`.

**`-u` en `git push -u origin main`:** configura el *upstream* (main local trackea
`origin/main`), así después alcanza con `git push`/`git pull` sin argumentos (se ve con
`git branch -vv`).

**¿Por qué falla el push en "Simulando colaboración"?** Porque el remoto tiene un commit
que el repo local no tiene (rechazo *fetch first / non-fast-forward*). Hay que hacer
`git pull` (fetch + merge), y recién ahí `git push`. Pull antes de push, siempre.

**Stash:** guarda los cambios sin commitear y deja el árbol limpio para cambiar de rama;
`git stash pop` los vuelve a aplicar y borra la entrada del stash.

**Rebase interactivo:** permite reescribir commits locales (`reword`, `squash`, reordenar).
En el script, tres commits con mensajes malos (`asdf`, `fix`, `otro fix`) quedan en uno
solo con un mensaje claro. Nunca se hace sobre commits ya pusheados: cambia los hashes y
a los demás les queda una historia que no coincide con la del remoto.

## Qué se probó

`bash practica_git.sh` corrió completo acá (git 2.43): primer repo, diff, show, blame,
merge fast-forward, conflicto provocado y resuelto, `.gitignore` (incluido el caso del
archivo ya trackeado), push con upstream a un remoto bare, push rechazado + pull + push,
stash y rebase interactivo con squash. Lo que no se puede probar acá es lo que pasa en la
web de GitHub (crear el repo privado, editar desde el navegador, agregar colaborador).
