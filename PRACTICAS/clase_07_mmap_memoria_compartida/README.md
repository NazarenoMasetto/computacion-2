# Clase 07 - mmap y memoria compartida

Todo en Python 3 (stdlib), probado en Linux con Python 3.13. Ningún programa espera señales
ni usa red: se corren directo y terminan solos. Los archivos de trabajo van a `/tmp` (como en la consigna)
o a un directorio temporal que se borra al final.

| Ejercicio | Archivo(s) | Cómo correrlo |
|---|---|---|
| 1.1 Crear y mapear un archivo | `ej1_1_mmap_archivo.py` | `python3 ej1_1_mmap_archivo.py` |
| 1.2 mmap solo lectura | `ej1_2_mmap_solo_lectura.py` | `python3 ej1_2_mmap_solo_lectura.py` (después de 1.1) |
| Tarea 1: buscar y reemplazar + `cat` | `ej1_tarea_reemplazo.py` | `python3 ej1_tarea_reemplazo.py && cat /tmp/mmap_tarea.txt` (opcional: `[archivo] [palabra] [reemplazo]`) |
| 2.1 Números binarios en mmap | `ej2_1_numeros_binarios.py` | `python3 ej2_1_numeros_binarios.py` |
| Tarea 2: registros id/nota/nombre | `ej2_tarea_registros.py` | `python3 ej2_tarea_registros.py` |
| 3.1 mmap anónimo padre-hijo | `ej3_1_mmap_anonimo_fork.py` | `python3 ej3_1_mmap_anonimo_fork.py` |
| 3.2 Hijos en regiones separadas | `ej3_2_hijos_regiones.py` | `python3 ej3_2_hijos_regiones.py` |
| Tarea 3: sumas parciales | `ej3_tarea_suma_parcial.py` | `python3 ej3_tarea_suma_parcial.py [hijos] [por_hijo]` (default 4 x 25 → 1..100) |
| 4.1 mmap + multiprocessing | `ej4_1_mmap_multiprocessing.py` | `python3 ej4_1_mmap_multiprocessing.py` |
| 5.1 Race con Value (obligatorio) | `ej5_1_race_value.py` | `python3 ej5_1_race_value.py [N]` (correrlo varias veces) |
| 5.2 Array compartido (obligatorio) | `ej5_2_array_cuadrados.py` | `python3 ej5_2_array_cuadrados.py` |
| Tarea 5: senos + Value (bonus) | `ej5_tarea_seno.py` | `python3 ej5_tarea_seno.py` y para ver la race: `python3 ej5_tarea_seno.py 200000` |
| 6.1 SharedMemory | `ej6_1_shared_memory.py` | `python3 ej6_1_shared_memory.py` |
| 6.2 ShareableList | `ej6_2_shareable_list.py` | `python3 ej6_2_shareable_list.py` |
| Síntesis: banco (tareas 1-3) | `sintesis_banco.py` | `python3 sintesis_banco.py` · tarea 2: `python3 sintesis_banco.py 10000` · tarea 3 (log): `python3 sintesis_banco.py 100 /tmp/banco.log` |
| Adicional: mmap como caché | `adicional_mmap_cache.py` | `python3 adicional_mmap_cache.py [MB]` (default 10 MB) |
| Adicional: chat con SharedMemory | `adicional_chat_shm.py` | `python3 adicional_chat_shm.py` |
| Adicional: monitor de temperatura | `adicional_monitor_temperatura.py` | `python3 adicional_monitor_temperatura.py [sensores] [segundos]` |

El checklist del obligatorio (ej. 5) queda cubierto entre `ej5_1` (Value + race + diferencia esperado/obtenido),
`ej5_2` (Array + reparto del trabajo + verificación de errores) y `ej5_tarea_seno.py`.

### Cosas que corregí del código de la consigna
- **1.1**: `mm.find(b"mmap")` devolvía `-1` y después `seek(-1)` explotaba con `ValueError`. `mmap.find()` busca **desde la posición actual**, y el `readline()` anterior dejó el puntero al final. Se arregla con `mm.find(b"mmap", 0)`.
- **6.2**: se reservaban 10 espacios para un string de 11 (`"actualizado"`). Funciona de casualidad porque `ShareableList` redondea a múltiplos de 8 bytes (16); con 17+ chars da `ValueError`. Reservé 15.
- Todo el código que crea procesos con `multiprocessing` está dentro de `main()` con `if __name__ == "__main__":`, así funciona también con `spawn`/`forkserver` (default desde Python 3.14).
- Los `unlink()` de SharedMemory están en un `finally`, para no dejar segmentos colgados en `/dev/shm` si algo falla.

## Qué se probó

Todos los scripts se corrieron con `timeout` y terminan bien:
- 1.1 encuentra `mmap` en la posición 53 y el archivo queda `MMAP`; 1.2 da `mmap can't modify a readonly memory map`; tarea 1: `cat` muestra `CLAVE` en la línea 2 y si los largos difieren el script avisa.
- 2.1/tarea 2: lectura correcta de los 10 enteros y de los 5 registros (28 bytes cada uno).
- 3.x: el padre lee lo que escribieron los hijos; tarea 3 da 5050 (y 32004000 con `8 1000`).
- 5.1: en 3 corridas se perdieron 254987, 238876 y 233662 incrementos de 400000. 5.2: 0 errores.
- Tarea 5: con 100 elementos la suma sin lock dio bien; con 200000 dio 339.04 en vez de 136.28 (con lock: exacta).
- Síntesis: con 100 transferencias, 2 de 6 corridas dieron mal el total (4968 y 5086); con 10000, las 3 corridas perdieron entre 1300 y 2650. El log registra 300 líneas.
- Caché (10 MB): secuencial ~igual (0.035 / 0.028 / 0.027 s); acceso aleatorio mmap ~8 veces más rápido (0.046 vs 0.006 s).
- Chat: 6 mensajes alternados sin pérdidas. Monitor: 3 sensores, estadísticas cada 0.5 s. `/dev/shm` queda limpio al terminar.

## Respuestas

**1.2 ¿Qué pasa al escribir en un mmap de solo lectura?** Tira `TypeError: mmap can't modify a readonly memory map`. Leer anda igual que siempre.

**Tarea 1 - ¿Por qué el reemplazo tiene que ser del mismo largo?** Porque el mmap tiene tamaño fijo: no podés insertar ni borrar bytes, solo pisarlos. El `cat` muestra el cambio porque el mapeo es `MAP_SHARED`: escribir en la memoria es escribir en el archivo (el `flush()` lo fuerza a disco).

**Tarea 2 - formato.** `'i f 20s'` ocupa 28 bytes (4 + 4 + 20). Usé `'='` adelante para que no meta padding de alineación y el tamaño sea predecible. Los nombres cortos se rellenan con `\x00`, que hay que sacar con `rstrip` al leer.

**3.x ¿Por qué el padre ve lo que escribió el hijo si después de `fork()` la memoria se copia?** Porque `mmap(-1, ...)` es anónimo pero **compartido** (`MAP_SHARED`): esas páginas no se copian con copy-on-write, padre e hijo apuntan a las mismas. Una variable común de Python sí se copiaría y el padre no vería el cambio. El `wait()` hace de sincronización: el padre lee recién cuando el hijo terminó. En 3.2 no hace falta lock porque cada hijo escribe en su propia región.

**4.1 ¿Por qué cada proceso abre el archivo?** Un objeto `mmap` no se puede pasar como argumento a un `Process` (no se serializa). Cada uno hace su propio `mmap` del mismo archivo y, al ser compartido, todos ven las mismas páginas.

**5.1 ¿Por qué se pierden incrementos?** `contador.value += 1` son tres pasos: leer, sumar, escribir. El `Value` tiene un lock, pero se toma por separado para la lectura y para la escritura, no para la operación completa. Dos procesos leen el mismo valor, los dos suman 1 y escriben lo mismo: se pierde uno. Cambia en cada corrida porque depende de cómo el scheduler intercala los procesos. Se arregla con `with contador.get_lock(): contador.value += 1`.

**5.2 ¿Por qué acá no hay errores?** Cada proceso escribe índices distintos y nadie lee lo que escribe otro: no hay datos compartidos en disputa.

**Tarea 5 bonus - ¿El total del Value es correcto?** Con 100 elementos casi siempre da bien (cada proceso hace 25 sumas y termina antes de que el otro arranque). Con muchos elementos hay race: con 200000 la suma sin lock dio cualquier cosa, y la que usa `get_lock()` dio exacta. (Diferencias de ~1e-12 serían por el orden de las sumas de floats, no por la race.)

**6.x SharedMemory vs mmap.** `SharedMemory` es un segmento con nombre (`/dev/shm/psm_...`), así que cualquier proceso se puede enganchar por nombre, aunque no sea hijo. Cada proceso hace `close()` y **uno solo** (el creador) hace `unlink()`; si nadie lo hace queda ocupando memoria hasta reiniciar. `ShareableList` fija el tipo y el tamaño máximo de cada elemento al crearse.

**Síntesis 1 - ¿El dinero se conserva?** No siempre: a veces el total da 5000 y a veces se pierde o aparece plata. Es la race de leer-modificar-escribir sobre `cuentas[origen]` y `cuentas[destino]` (y además el chequeo `>= monto` y la resta no son atómicos, así que un saldo podría quedar negativo).

**Síntesis 2 - ¿Con 10000 se nota más?** Sí, mucho: con 100 transferencias a veces sale bien, con 10000 falla siempre y por más plata, porque hay muchas más chances de que dos cajeros se intercalen sobre la misma cuenta.

**Síntesis 3 - log.** Cada cajero abre el archivo en modo append (`O_APPEND`): cada línea se agrega al final de forma atómica, así no se pisan entre procesos. Usé archivo y no `ShareableList` porque la lista tiene tamaño fijo y además habría que sincronizar el índice de escritura (otra race).

**Síntesis 4 - ¿Cómo se resuelve?** Haciendo que la transferencia completa (chequeo + resta + suma) sea una sección crítica: con un `Lock` compartido (por ejemplo `cuentas.get_lock()` o un `multiprocessing.Lock`) alrededor de las tres operaciones. Una mejora es un lock por cuenta, tomándolos siempre en el mismo orden (por número de cuenta) para no generar deadlocks.

**Adicional caché - ¿qué conviene?** Para leer todo de corrido la diferencia es mínima (todo termina siendo copiar de la page cache). Donde mmap gana es en el acceso aleatorio: con `seek()+read()` cada lectura son 2 syscalls; con mmap es un acceso a memoria y el kernel resuelve las páginas con page faults.

**Adicional chat - ¿por qué el flag se escribe último?** Porque es lo que "publica" el mensaje: si se pusiera antes del texto, el otro proceso podría leer un mensaje a medio escribir. Igual es polling (gasta CPU esperando); con un `Event` o un semáforo sería más prolijo.

**Adicional monitor.** Cada sensor escribe solo su casillero (no hay race entre sensores); el monitor copia todo el array con el lock tomado para tener una foto coherente. Un `Value` compartido (`activo`) sirve como flag para que todos terminen.
