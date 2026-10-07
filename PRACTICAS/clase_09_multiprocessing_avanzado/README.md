# Clase 9: Multiprocessing avanzado

Solo stdlib, Python 3.10+. No hay servidores en esta clase.

| Ejercicio | Archivo(s) | Comando |
|---|---|---|
| 1. Métodos de Pool | `ej1_metodos_pool.py` | `python3 ej1_metodos_pool.py` (duración variable) / `python3 ej1_metodos_pool.py 0.3 0.3` (duración constante) |
| 2. Secuencial vs paralelo | `ej2_speedup.py` | `python3 ej2_speedup.py` |
| 3. Value y Array | `ej3_value_array.py` | `python3 ej3_value_array.py` / `python3 ej3_value_array.py --sin-lock` |
| 4. Manager | `ej4_manager.py` | `python3 ej4_manager.py` |
| 5. Procesador de imágenes (obligatorio) | `ej5_procesador_imagenes.py` | `python3 ej5_procesador_imagenes.py [num_imgs] [size] [workers]` (default 8 200 4) |
| 6. Map-Reduce | `ej6_map_reduce.py` | `python3 ej6_map_reduce.py` / extensión: `python3 ej6_map_reduce.py archivo_grande.txt 5000` |
| 7. Pipeline | `ej7_pipeline.py`, `ej7b_pipeline_etapa_lenta.py` | `python3 ej7_pipeline.py` / `python3 ej7b_pipeline_etapa_lenta.py` |
| Adicional: pi Monte Carlo | `ej8_montecarlo_pi.py` | `python3 ej8_montecarlo_pi.py [puntos] [workers]` |
| Adicional: merge sort paralelo | `ej9_merge_sort_paralelo.py` | `python3 ej9_merge_sort_paralelo.py [workers]` |
| Adicional: procesador de archivos | `ej10_procesador_archivos.py` | `python3 ej10_procesador_archivos.py /usr/lib/python3.13/json "def"` |

## Qué se probó

Todos los scripts se corrieron en Linux con Python 3.13 en una máquina de **2 cores** (los tiempos de abajo
son de esa máquina y van a cambiar en otra). El ej3 se corrió con y sin lock, el ej6 también con un archivo
de 200.000 líneas (40 chunks), el ej5 verifica que el checksum paralelo sea igual al secuencial y el ej9
verifica que el resultado sea igual a `sorted()`.

Tiempos obtenidos (ej2, N=500.000, 8 tareas, 2 cores):

| Modo | Tiempo | Speedup |
|---|---|---|
| Secuencial | 0.51 s | 1.00x |
| Pool(1) | 0.54 s | 0.94x |
| Pool(2) | 0.41 s | 1.24x |
| Pool(4) | 0.45 s | 1.13x |
| Pool(8) | 0.95 s | 0.53x |

Otros: ej5 speedup ~1.3x con 4 workers; Monte Carlo (4M puntos) 1.37 s → 0.69 s (≈2x); pipeline 10 items 0.63 s contra ~1.5 s secuencial.

## Respuestas

**Ej 1**
- *¿Por qué `imap_unordered` puede ser más rápido que `imap`?* Porque te entrega cada resultado apenas termina, sin esperar a que terminen los anteriores. Con `imap`, si la tarea 0 es lenta, los resultados 1..7 ya listos quedan "trabados" esperando (en la corrida se ve: con `imap` todo llegó junto a los 0.93 s; con `imap_unordered` el primero llegó a los 0.45 s). Podés ir procesando antes y el consumidor no se queda ocioso.
- *¿Cuándo conviene `apply_async` en vez de `map`?* Cuando las tareas son heterogéneas (distintas funciones o argumentos), cuando querés lanzarlas de a una a medida que aparecen, usar callbacks/`error_callback`, o hacer `get(timeout=...)` por tarea en vez de esperar todo el lote.
- *¿Y si la duración fuera constante?* Las tareas terminan prácticamente en orden de a tandas de 4, así que `imap` e `imap_unordered` dan casi el mismo orden y los mismos tiempos (probado con `0.3 0.3`: ambas en dos tandas a 0.30 s y 0.60 s; sólo cambia algún orden dentro de una tanda).

**Ej 2** — Lo esperable es speedup ≈ N hasta llegar a la cantidad de cores. Con 2 cores el máximo fue con Pool(2) (1.24x; no llega a 2x por el overhead de crear procesos y porque la tarea es corta, ~0.5 s en total). Pool(1) es un poco más lento que secuencial (mismo trabajo + overhead). Con 4 y 8 workers no mejora y hasta empeora: hay más procesos que cores, así que se pelean por la CPU y se suma el costo de crearlos.

**Ej 3**
- *¿Sin `get_lock()`?* Aparece la race condition: `contador.value += 1` es leer-sumar-escribir, dos procesos leen el mismo valor y uno pisa al otro. En la prueba dio 20669 en vez de 40000 (varía en cada corrida).
- *¿Lock para el Array?* No, porque cada worker escribe en un segmento distinto (índices disjuntos) y nadie lee lo que escribe otro mientras trabaja. No hay dato compartido en conflicto. Igual, `Array` trae lock por defecto, pero acá no hace falta usarlo.

**Ej 4**
- *¿Orden de la lista?* Por orden de finalización (el que duerme menos hace `append` primero), no por id. Por eso es "aleatorio" entre corridas. El dict lo muestro ordenado por clave.
- *¿Manager vs Value/Array?* Manager es bastante más lento: cada acceso es un mensaje (pickle + socket/pipe) a un proceso servidor aparte. `Value`/`Array` son memoria compartida real, se accede directo. A cambio, Manager soporta estructuras complejas (dict, list anidados) e incluso procesos en otras máquinas.

**Ej 5** — Cumple todo lo pedido: imágenes aleatorias, blur 3x3, `Pool.map`, tiempos secuencial vs paralelo, speedup y `if __name__ == "__main__"`. El speedup (~1.3x con 2 cores) es menor a 2 porque hay que serializar las matrices (pickle) para mandarlas a los workers y devolver el resultado.

**Ej 6 (extensión)** — Con un archivo se lee por chunks de N líneas con un generador (no se carga todo en memoria) y se usa `imap_unordered` porque el reduce (suma de conteos) es conmutativo, el orden no importa.

**Ej 7**
- *¿Si una etapa es mucho más lenta?* Se vuelve el cuello de botella: el throughput de todo el pipeline queda limitado por esa etapa, su cola de entrada se va llenando y las etapas siguientes quedan esperando. En `ej7b` con la etapa del medio 4 veces más lenta: 2.53 s.
- *¿Cómo escalarla?* Poniendo varios workers de esa etapa leyendo de la misma cola (o un `Pool` dentro de la etapa). Hay que mandar un `None` por cada worker y que la etapa siguiente espere tantos `None` como workers haya antes de terminar. Con 4 workers en la etapa lenta bajó a 0.89 s. Ojo: con varios workers el orden de salida puede cambiar.

**Merge sort paralelo — ¿a partir de qué tamaño conviene?** En la máquina de prueba (2 cores), para listas chicas (1.000–10.000) el paralelo es mucho más lento (crear el Pool y hacer pickle cuesta más que ordenar). Alrededor de 50.000 elementos empezó a convenir (1.2x). Para listas más grandes no mejoró (0.84–0.9x) porque el último merge lo hace el padre secuencialmente y mandar/recibir listas enormes por pickle es caro; en mi máquina el resultado es irregular. Conclusión: conviene recién con decenas de miles de elementos y con más cores; para ordenar en serio, `sorted()` (en C) le gana a todo esto.

## Salteado

Nada; `extra_manijas.md` no se hizo (por consigna).
