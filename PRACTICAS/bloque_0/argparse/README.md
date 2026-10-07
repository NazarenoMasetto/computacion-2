# Bloque 0 — Argumentos de línea de comandos (sys.argv / argparse)

Todos los scripts usan solo la stdlib, salvo `tareas_click.py` (requiere `click`)
y el autocompletado opcional de `tareas.py` (requiere `argcomplete`).
Todos tienen `--help` (los de la Parte 1 usan `sys.argv` a propósito) y salen
con código 0 si anduvo bien y distinto de 0 si hubo error.

## Ejercicios

| Ejercicio | Archivo | Cómo correrlo (desde esta carpeta) |
|---|---|---|
| 1.1 Saludo | `saludo.py` | `python3 saludo.py Juan` |
| 1.2 Suma | `suma.py` | `python3 suma.py 1 2 3 4 5` |
| 1.3 Contador de líneas | `wc_simple.py` | `python3 wc_simple.py saludo.py` |
| 2.1 Temperatura | `temperatura.py` | `python3 temperatura.py 100 --to fahrenheit` |
| 2.2 Listador | `listar.py` | `python3 listar.py /tmp -a --extension .txt` |
| 2.3 Contraseñas | `genpass.py` | `python3 genpass.py --count 3 -n 16 --no-symbols` |
| **3.1 Mini-grep (OBLIGATORIO)** | `buscar.py` | `python3 buscar.py "TODO" *.py -i` / `cat buscar.py \| python3 buscar.py import -n` |
| 3.2 Procesador JSON | `jsonproc.py` | `python3 jsonproc.py datos.json --get usuario.nombre` / `echo '{"a": 1}' \| python3 jsonproc.py - --get a` |
| 3.3 Gestor de tareas | `tareas.py` | `python3 tareas.py add "Estudiar" --priority alta` · `list` · `done 1` · `remove 1` |
| 4.1 Tareas con Click | `tareas_click.py` | `pip install click` y `python3 tareas_click.py list` |
| 4.2 Autocompletado | `tareas.py`, `tareas_click.py` | ver sección "Autocompletado" |
| 4.3 Configuración en capas | `jsonproc.py` | `JSONPROC_INDENT=2 python3 jsonproc.py datos.json --pretty` |

### Detalles de uso

- **buscar.py**: el patrón es una expresión regular (`re.search`). Sin archivos lee
  de stdin (si stdin es una terminal, avisa y sale). Con varios archivos el `-n` va
  por default. Salida: `archivo:N: línea` (con `-n` o varios archivos), `archivo: línea`
  (un archivo sin `-n`) o la línea sola (stdin). Códigos de salida como `grep`:
  0 = hubo coincidencias, 1 = no hubo, 2 = error (archivo ilegible o patrón inválido).
  Nota: en el primer ejemplo de la consigna `"error"` encuentra `"Error"` sin `-i`;
  eso no es coherente con el ejemplo de `-i`, así que la búsqueda es sensible a
  mayúsculas salvo que se pase `-i` (como el grep real).
- **jsonproc.py**: `--keys`, `--get` y `--set` son excluyentes; `--pretty` y `-o` se
  combinan con cualquiera. `--set KEY VALUE` interpreta VALUE como JSON si puede
  (`true`, `3`, `{"x":1}`) y si no lo guarda como string; crea los diccionarios
  intermedios que falten. Sin acción, imprime el JSON compacto.
- **tareas.py / tareas_click.py**: guardan en `~/.tareas.json` (el mismo formato, se
  pueden usar indistintamente). `remove` pide confirmación `[s/N]`; con `-y` no pregunta.
  Para probar sin tocar tu home real: `HOME=$(mktemp -d) python3 tareas.py add prueba`.

### Configuración en capas (4.3)

Precedencia: **CLI > variables de entorno > `~/.jsonprocrc` > defaults** (`indent=4`, `sort_keys=false`).

```bash
echo '{"indent": 1, "sort_keys": true}' > ~/.jsonprocrc     # (YAML si tenés PyYAML)
python3 jsonproc.py datos.json --pretty                       # usa indent 1, ordenado
JSONPROC_INDENT=6 python3 jsonproc.py datos.json --pretty     # el entorno pisa al archivo
JSONPROC_INDENT=6 python3 jsonproc.py datos.json --pretty --indent 2 --no-sort-keys   # la CLI pisa todo
```

### Autocompletado (4.2)

- **argparse + argcomplete** (`tareas.py` ya tiene el marcador `# PYTHON_ARGCOMPLETE_OK`
  y llama a `argcomplete.autocomplete(parser)` si la librería está instalada):
  ```bash
  pip install "argcomplete>=3.3"        # con Python 3.13 hace falta una versión nueva
  chmod +x tareas.py
  eval "$(register-python-argcomplete tareas.py)"
  ./tareas.py <TAB><TAB>                # add  done  list  remove
  ./tareas.py list --<TAB><TAB>         # --done  --pending  --priority
  ```
- **Click** (nativo): el script fija `prog_name="tareas-click"`, así que la variable es
  `_TAREAS_CLICK_COMPLETE`:
  ```bash
  alias tareas-click="python3 $PWD/tareas_click.py"   # o un symlink en el PATH
  eval "$(_TAREAS_CLICK_COMPLETE=bash_source python3 tareas_click.py)"
  tareas-click <TAB><TAB>
  ```

## Respuestas

**1.1 — ¿Qué pasa con `python saludo.py María Elena`?** La shell separa por espacios,
así que llegan dos argumentos (`argv[1]="María"`, `argv[2]="Elena"`) y se saluda solo a
"María". Para saludar "María Elena" hay dos caminos: que el usuario use comillas
(`python saludo.py "María Elena"`, llega un solo argumento) o unir todo en el código con
`" ".join(sys.argv[1:])`. El script deja el comportamiento del ejemplo y lo comenta.

**1.2 — Robustez:** cada argumento se intenta convertir con `int()` y si no con `float()`;
si falla, se muestra `Error: 'hola' no es un número válido` y sale con código 1, sin traceback.

**1.3 — Por qué `sys.argv` se vuelve tedioso:** hay que validar a mano la cantidad de
argumentos, los tipos, el mensaje de uso y los errores de archivo en cada script.
argparse hace todo eso (más `--help`) declarativamente.

**4.1 — argparse vs Click** (`tareas.py` 146 líneas vs `tareas_click.py` ~100, con la misma
funcionalidad):
- *Menos líneas:* Click. Los decoradores eliminan el armado del parser, los `set_defaults(func=...)`
  y el despacho a mano; `ClickException` resuelve los errores amigables.
- *Más fácil de leer:* Click, porque cada comando tiene sus opciones pegadas a la función
  que las usa. argparse obliga a mirar dos lugares (el parser y la función).
- *Mejor experiencia de usuario:* parecidas. Click trae autocompletado nativo, `confirm`/`prompt`
  y mejores mensajes de "Did you mean...?"; argparse tiene la ventaja de no necesitar instalar
  nada y de soportar grupos excluyentes nativos (en Click el `--pending`/`--done` excluyente se
  validó a mano). Detalle: `click.confirm` usa `y/N` en inglés, por eso se usó `click.prompt`
  para el `[s/N]`.

## Qué se probó

Todo se corrió acá (Python 3.13) con los ejemplos de la consigna y casos de error:
saludo/suma/wc_simple (incluido `suma.py hola` y archivo inexistente), temperatura (incluido
`--help` y faltante de `-t`), listar (ocultos, extensión, directorio inexistente), genpass
(todas las opciones), buscar (`-i`, `-n`, `-c` con total, `-v`, stdin por pipe, varios archivos,
archivo inexistente, regex inválida, códigos de salida), jsonproc (`--keys`, `--get` con
índices, `--pretty`, `--set ... -o`, stdin con `-`, rutas inválidas y las tres capas de
config), tareas y tareas_click (add/list con filtros/done/remove con confirmación s y N, ID
inexistente) con `HOME` temporal. El autocompletado se probó simulando la shell
(`_ARGCOMPLETE=1 COMP_LINE=...` y `_TAREAS_CLICK_COMPLETE=bash_complete`): devuelve
`add list done remove` y `--pending --done --priority`. Ojo: el `argcomplete` 3.1 del sistema
falla con Python 3.13; con 3.7 (venv) anda bien.
