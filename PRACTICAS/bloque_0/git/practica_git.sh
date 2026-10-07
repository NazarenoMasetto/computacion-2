#!/usr/bin/env bash
# Práctica de Git (bloque 0) hecha de punta a punta en un directorio temporal.
# Cubre: Parte 1 (fundamentos), Parte 2 (branches, conflictos, .gitignore),
# Parte 3 (remoto y colaboración, simulando GitHub con un repo "bare" local)
# y los ejercicios extra (stash y rebase interactivo).
#
# Es seguro: todo pasa dentro de un mktemp -d; no toca tu configuración global
# de git (el usuario se configura solo en los repos temporales).
#
# Uso:  bash practica_git.sh            (deja el directorio para que lo mires)
#       BORRAR=1 bash practica_git.sh   (lo borra al terminar)
set -euo pipefail

BASE=$(mktemp -d -t practica-git-XXXXXX)
if [[ "${BORRAR:-0}" == "1" ]]; then
    trap 'rm -rf "$BASE"' EXIT
fi
export GIT_PAGER=cat PAGER=cat       # que git log/show no abran el paginador
export GIT_EDITOR=true               # que ningún commit abra un editor

titulo() { echo; echo "=================== $* ==================="; }
cmd()    { echo "\$ $*"; "$@"; }

# Identidad SOLO para estos repos (placeholders, sin datos reales)
config_local() {
    git config user.name "Alumno Ejemplo"
    git config user.email "alumno@example.com"
}

cd "$BASE"
echo "Trabajando en: $BASE"

# ---------------------------------------------------------------------------
titulo "PARTE 1 - Tu primer repositorio"
cmd mkdir ejercicio-git
cd ejercicio-git
cmd git init -b main
config_local
cmd ls -la

echo "# Mi primer repositorio" > README.md
echo "Nombre: [tu nombre]" >> README.md
echo "Legajo: [tu legajo]" >> README.md
cmd git status                       # README.md aparece como untracked
cmd git add README.md
cmd git status                       # ahora en "Changes to be committed"
cmd git commit -m "Agregar README con datos personales"
cmd git log --oneline

# ---------------------------------------------------------------------------
titulo "PARTE 1 - El ritmo de trabajo"
echo 'print("Hello World")' > main.py
cmd git status                       # main.py untracked
cmd git add main.py
cmd git commit -m "Agregar programa inicial"

echo 'print("Hola, soy [tu nombre]")' > main.py
cmd git diff                         # muestra la línea quitada (-) y la agregada (+)
cmd git add main.py
cmd git commit -m "Personalizar mensaje de saludo"
cmd git log --oneline                # dos commits nuevos (tres en total)

# ---------------------------------------------------------------------------
titulo "PARTE 1 - Explorando la historia"
cmd git log
cmd git log --oneline
HASH=$(git log --format=%h -1 HEAD~1)   # el commit "Agregar programa inicial"
cmd git show "$HASH"
cmd git blame main.py

# ---------------------------------------------------------------------------
titulo "PARTE 2 - Trabajando con branches"
cmd git branch feature-suma
cmd git switch feature-suma
cmd git branch                       # el * marca la rama actual
cat > main.py <<'PY'
def suma(a, b):
    return a + b

print("Hola, soy [tu nombre]")
print(f"2 + 3 = {suma(2, 3)}")
PY
cmd git add main.py
cmd git commit -m "Agregar función suma"
cmd git switch main
echo "--- main.py en main (no tiene la función suma):"
cat main.py
cmd git merge feature-suma           # fast-forward: main no avanzó
echo "--- main.py en main después del merge:"
cat main.py
cmd python3 main.py
cmd git log --oneline --graph --all

# ---------------------------------------------------------------------------
titulo "PARTE 2 - Resolviendo conflictos"
cmd git switch -c version-a
sed -i '1s/.*/# Repositorio de práctica (versión A)/' README.md
cmd git commit -am "Cambiar título en version-a"
cmd git switch main
sed -i '1s/.*/# Repositorio de práctica (versión main)/' README.md
cmd git commit -am "Cambiar título en main"

echo "\$ git merge version-a   (va a dar conflicto, es lo esperado)"
if git merge version-a; then
    echo "¡No hubo conflicto! (no debería pasar)"
else
    echo "--- README.md con los marcadores de conflicto:"
    cat README.md
    cmd git status
    # Resolución: combinamos las dos versiones en una sola línea
    sed -i '/^<<<<<<< /d; /^=======$/d; /^>>>>>>> /d' README.md
    sed -i '1,2c # Repositorio de práctica (versión main + versión A)' README.md
    echo "--- README.md resuelto:"
    cat README.md
    cmd git add README.md
    cmd git commit --no-edit         # usa el mensaje de merge por defecto
fi
cmd git log --oneline --graph --all

# ---------------------------------------------------------------------------
titulo "PARTE 2 - Ignorando archivos"
# Un venv real tarda un poco; si falla (falta python3-venv) creamos la carpeta igual
python3 -m venv venv 2>/dev/null || mkdir -p venv/bin
echo "SECRET=mi_clave_secreta" > .env
mkdir -p __pycache__ && touch __pycache__/test.pyc
cmd git status --short               # aparecen venv/, .env y __pycache__/
printf 'venv/\n.env\n__pycache__/\n' > .gitignore
cmd git status --short               # solo queda .gitignore
cmd git add .gitignore
cmd git commit -m "Agregar .gitignore"

# Demostración de la advertencia: un archivo ya trackeado NO se ignora
echo "debug=1" > config.local
cmd git add config.local
cmd git commit -m "Commitear config.local (por error)"
echo "config.local" >> .gitignore
echo "debug=2" > config.local
cmd git status --short               # config.local sigue apareciendo como modificado
cmd git rm --cached config.local     # lo sacamos del repo (queda en disco)
cmd git commit -am "Dejar de trackear config.local"
cmd git status --short               # ahora sí está ignorado

# ---------------------------------------------------------------------------
titulo "PARTE 3 - Subir a un remoto (simulamos GitHub con un repo bare)"
cmd git init --bare -b main "$BASE/github-ejercicio-git.git"
cmd git remote add origin "$BASE/github-ejercicio-git.git"
cmd git push -u origin main
cmd git branch -vv                   # main trackea origin/main

# ---------------------------------------------------------------------------
titulo "PARTE 3 - Simulando colaboración"
# Otro clon hace de "edición desde la web de GitHub"
cmd git clone "$BASE/github-ejercicio-git.git" "$BASE/clon-web"
(
    cd "$BASE/clon-web"
    config_local
    echo "Línea agregada desde la web" >> README.md
    git commit -qam "Editar README desde GitHub"
    git push -q
)
# Cambio local en un archivo distinto (así el pull mergea sin conflicto)
echo "Otra línea" >> notas.txt
cmd git add notas.txt
cmd git commit -m "Agregar línea localmente"
echo "\$ git push   (va a ser rechazado: el remoto tiene commits que no tenemos)"
git push || echo ">>> push rechazado, como se esperaba"
cmd git pull --no-rebase --no-edit   # integra los cambios del remoto (merge)
cmd git push
cmd git log --oneline --graph --all

# ---------------------------------------------------------------------------
titulo "EXTRA - Stash"
cmd git switch -c otra-cosa
cmd git switch main
echo "trabajo a medio hacer" >> main.py
cmd git status --short
cmd git stash                        # guarda el cambio y deja el árbol limpio
cmd git status --short
cmd git switch otra-cosa
echo "arreglo urgente" > urgente.txt
cmd git add urgente.txt
cmd git commit -m "Arreglo urgente"
cmd git switch -
cmd git stash pop                    # recuperamos el trabajo
cmd git status --short
git checkout -- main.py              # descartamos el cambio de prueba

# ---------------------------------------------------------------------------
titulo "EXTRA - Rebase interactivo (sobre commits LOCALES, no pusheados)"
echo "a" > rebase.txt; git add rebase.txt; git commit -qm "asdf"
echo "b" >> rebase.txt; git commit -qam "fix"
echo "c" >> rebase.txt; git commit -qam "otro fix"
cmd git log --oneline -4
# git rebase -i abre un editor con la lista de commits. Para hacerlo sin
# interacción usamos GIT_SEQUENCE_EDITOR con sed:
#   - 1er commit: reword (cambiar mensaje)
#   - 2do y 3ro: squash (combinarlos con el anterior)
GIT_SEQUENCE_EDITOR="sed -i -e '1s/^pick/reword/' -e '2,3s/^pick/squash/'" \
GIT_EDITOR="sh -c 'printf \"Agregar rebase.txt con tres líneas\n\" > \"\$1\"' --" \
    git rebase -i HEAD~3
echo "\$ git log --oneline -3   (los 3 commits quedaron en uno con buen mensaje)"
git log --oneline -3
cmd cat rebase.txt

titulo "LISTO"
echo "Todo quedó en: $BASE"
[[ "${BORRAR:-0}" == "1" ]] && echo "(se borra al salir porque BORRAR=1)"
exit 0
