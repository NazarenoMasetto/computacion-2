# Clase 11 - Sincronización

Todo probado en Linux con Python 3.13 (stdlib). Los ejemplos que se cuelgan a propósito se corrieron con `timeout`.

| Ejercicio | Archivo(s) | Comando |
|---|---|---|
| 1.1 Cuenta con race condition | `ej1_1_cuenta_insegura.py` | `python3 ej1_1_cuenta_insegura.py` |
| 1.2 Cuenta corregida (TODO) | `ej1_2_cuenta_segura.py` | `python3 ej1_2_cuenta_segura.py` |
| 2 Productor-consumidor con Condition | `ej2_productor_consumidor.py` | `python3 ej2_productor_consumidor.py` |
| 3 Barrier por fases | `ej3_barrier_fases.py` | `python3 ej3_barrier_fases.py` |
| 4 Pool con Semaphore | `ej4_pool_semaforo.py` | `python3 ej4_pool_semaforo.py` |
| 5 Readers-Writers (obligatorio) | `ej5_readers_writers.py` | `python3 ej5_readers_writers.py` |
| 6 Deadlock y prevención | `ej6_deadlock.py` | `python3 ej6_deadlock.py` |
| 7A Filósofos con Barrier (se cuelga) | `ej7_filosofos.py` | `timeout 5 python3 ej7_filosofos.py A` (o Ctrl+C) |
| 7A sin barrera, N corridas | `ej7_filosofos.py` | `python3 ej7_filosofos.py A-sin-barrera 10` |
| 7B Jerarquía de recursos | `ej7_filosofos.py` | `python3 ej7_filosofos.py B` |
| 7C Semaphore(N-1) | `ej7_filosofos.py` | `python3 ej7_filosofos.py C` |
| 7D Comparación / medición | `ej7_filosofos.py` | `python3 ej7_filosofos.py D` |
| Adicional: monitor de recursos | `ej_adicional_monitor.py` | `python3 ej_adicional_monitor.py 3` |
| Adicional: rate limiter | `ej_adicional_rate_limiter.py` | `python3 ej_adicional_rate_limiter.py 10 5 6` |

## Qué se probó (resultados reales)

- **1.1**: el saldo final no coincide con el esperado (ej. esperado 1380, obtenido 1100). En la consigna el "esperado" decía 1000, pero como las operaciones son al azar eso no es correcto: el script calcula el esperado sumando depósitos y retiros exitosos de cada thread.
- **1.2**: `CuentaInsegura` 0/3 corridas bien; `CuentaSegura` 3/3, y un `assert` lo verifica.
- **2**: se consumen los 10 items, todos los threads terminan.
- **3**: resultado final `[20, 60, 100, 60]`, igual al calculado a mano.
- **4**: 30 requests y nunca hay más de 3 conexiones en uso a la vez (se agregó ese contador).
- **5**: 3 corridas: 25 lecturas, 6 escrituras, hasta 5 lectores simultáneos y 0 violaciones de exclusión (instrumentado con un contador aparte).
- **6**: detecta el deadlock a los 2 s y la versión corregida termina. Cambio: los threads con deadlock son `daemon=True`; si no, el programa nunca termina porque el intérprete espera a esos threads trabados.
- **7A**: con Barrier se cuelga siempre (`timeout` lo mata, exit 124). Sin barrera: 0 de 10 corridas colgadas y **2 de 200**.
- **7B / 7C**: terminan siempre, 3 comidas cada uno.
- **7D** (una corrida):

| Solución | Tiempo para 3 comidas (prom.) | Comidas en 2 s | min/max |
|---|---|---|---|
| B jerarquía | ~22 ms | `[288, 339, 367, 395, 287]` | 0.73 |
| C semáforo | ~25 ms | `[177, 178, 178, 176, 176]` | 0.99 |

- **Adicionales**: el monitor muestra el dueño del lock y los threads adentro/esperando en el semáforo. El rate limiter hace 30 ops con límite 10/s en ~2 s, nunca más de 10 en una ventana de 1 s, y `try_acquire` deja pasar exactamente 10 en una ráfaga.

## Respuestas

**Ej. 5: decisiones del RW lock.** La versión de la consigna da prioridad a los lectores: si siempre hay alguno leyendo, el escritor no entra nunca (starvation). Agregué `writers_waiting`: si hay un escritor esperando, los lectores nuevos no entran, y al soltar la escritura se le pasa el turno a otro escritor o se despierta a todos los lectores (`notify_all`). Usa dos `Condition` sobre el mismo `Lock` y context managers `ReadLock`/`WriteLock`. Ojo: en el test, `datos["lecturas"] += 1` lo hacen varios lectores a la vez (el read lock no da exclusión), así que lo protegí con un lock aparte.

**Ej. 7A: ¿qué condiciones de Coffman se cumplen?** Las cuatro:
1. Exclusión mutua: un tenedor (`Lock`) lo tiene un solo filósofo.
2. Retención y espera: cada uno se queda con el izquierdo mientras espera el derecho.
3. No apropiación: nadie le puede sacar el tenedor a otro.
4. Espera circular: 0 espera a 1, 1 a 2, ..., y 4 espera a 0.

**Ej. 7A: ¿cuántas veces se cuelga sin barrera?** En 10 corridas, ninguna. Hicieron falta 200 para ver 2. Por eso los deadlocks son difíciles de testear: el bug está siempre en el código, pero solo se manifiesta con un entrelazado puntual y poco probable.

**Ej. 7C: ¿por qué alcanza con N-1?** Con 4 filósofos y 5 tenedores, por el principio del palomar al menos uno consigue los dos tenedores, come y los suelta, y así destraba al resto. Nunca se puede cerrar el ciclo de 5.

**Ej. 7D: ¿alguna solución deja comiendo menos a alguno? ¿Cómo medirlo?** Sí, la jerarquía. Los filósofos 0 y 4 piden primero el tenedor 0 (los dos compiten por el mismo "primer" recurso) y comen ~25% menos que el 3. El semáforo, en esta corrida, quedó casi perfectamente parejo, pero es más lento (~25 vs ~22 ms) porque limita la concurrencia. Para medirlo no sirve fijar 3 comidas por cabeza, porque así todos comen 3 sí o sí. Hay que dejarlos comer durante un tiempo fijo y contar comidas por filósofo (relación min/max y desvío), además de medir la espera media por comida.

**Pregunta 1: ¿por qué la Barrier vuelve seguro el deadlock?** Porque obliga a que los 5 tengan el izquierdo antes de que alguno pida el derecho: fuerza justo el entrelazado que arma la espera circular. Sin la barrera, ese entrelazado también es posible, solo que pasa rara vez. La barrera no agrega el bug, lo hace reproducible.

**Pregunta 2: ¿qué condición rompe el semáforo?** Sigue siendo, en el fondo, la espera circular, porque no pueden estar los 5 en el ciclo. Pero lo que ataca directamente es la **retención y espera** sobre todo el conjunto: limita cuántos pueden retener un tenedor mientras esperan otro, y siempre queda uno libre. Exclusión mutua y no apropiación siguen intactas.

**Pregunta 3: ¿comer distinta cantidad es deadlock o starvation?** No es deadlock, porque el sistema avanza. Si un filósofo pudiera quedarse esperando indefinidamente sin comer nunca, sería starvation. Lo que medimos (unos comen 25% menos pero todos comen) es falta de equidad (fairness): no llega a ser ni una cosa ni la otra.

## Salteado

Nada de `ejercicios.md`. `extra_manijas.md` no se hizo (por consigna).
