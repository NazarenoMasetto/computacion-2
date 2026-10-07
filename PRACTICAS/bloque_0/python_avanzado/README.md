# Bloque 0 - Python avanzado

Todo en Python 3.10+ con stdlib. Cada archivo tiene docstrings, type hints y un bloque
`if __name__ == "__main__":` con ejemplos (incluyendo casos borde) que se pueden correr directo.

| Ejercicio | Archivo | Cómo correrlo |
|-----------|---------|---------------|
| 1.1 Context manager `archivo_temporal` | `archivo_temporal.py` | `python3 archivo_temporal.py` |
| 1.2 Decorador `@log_llamada` | `log_llamada.py` | `python3 log_llamada.py` |
| 1.3 Generador `fibonacci` | `fibonacci.py` | `python3 fibonacci.py` |
| **2.1 `Timer` (OBLIGATORIO)** | `timer.py` (clase `Timer` y función `timer` con `@contextmanager`) | `python3 timer.py` |
| **2.2 `@retry` (OBLIGATORIO)** | `retry.py` | `python3 retry.py` (el primer ejemplo es aleatorio, como en la consigna) |
| 2.3 Generador `chunked` | `chunked.py` | `python3 chunked.py` |
| 2.4 `pipeline` (+ bonus decorador) | `pipeline.py` | `python3 pipeline.py` |
| 3.1 `@memoize` | `memoize.py` | `python3 memoize.py` |
| 3.2 `Transaction` | `transaction.py` | `python3 transaction.py` |
| 3.3 `BufferedReader` | `buffered_reader.py` | `python3 buffered_reader.py` |
| 3.4 `@validate_types` | `validate_types.py` | `python3 validate_types.py` |
| 4.1 Decorador flexible | `decorador_flexible.py` | `python3 decorador_flexible.py` |
| 4.2 Scheduler de coroutines | `scheduler.py` | `python3 scheduler.py` |
| 4.3 Singleton con metaclase | `singleton.py` | `python3 singleton.py` |
| 4.4 Descriptor `Positivo` | `positivo.py` | `python3 positivo.py` |

Para usarlos desde otro código: `from timer import Timer`, `from retry import retry`, etc.

Notas de diseño:
- `archivo_temporal` se niega a usar un nombre que ya existe (si no, lo borraría al salir).
- `Timer.elapsed` es una property: durante el bloque da el parcial y después el total. Usa `time.perf_counter()`.
- `retry` acepta `exceptions` como tupla o una sola clase; las excepciones que no están en la tupla no se reintentan. Relanza la última con `raise`.
- `chunked` valida `n` apenas se llama (función normal que devuelve un generador interno).
- `pipeline` como decorador: si recibe exactamente una función definida con `def`, la decora (ejecuta la función y pasa su resultado por el pipeline). Sin funciones es la identidad.
- `memoize`: con `fibonacci(100)` da `CacheInfo(hits=98, misses=101, size=101)`. El número de hits de la consigna es ilustrativo; con memoización cada `fib(n)` calcula `fib(n-1)` (miss) y `fib(n-2)` ya está cacheado (hit), por eso hits = n-2. Argumentos no hasheables se ejecutan sin cachear.
- `Transaction` usa copia profunda (así también revierte un `append` a una lista), borra atributos agregados durante la transacción y soporta objetos con `__slots__`.
- `BufferedReader` lee bytes y usa un decoder incremental para no partir caracteres UTF-8 multibyte entre bloques. Entrega las líneas con su `\n`, igual que iterar un archivo.
- `validate_types` soporta tipos simples, `Any`, `Optional`/`Union`/`X | Y` y genéricos (`list[int]` chequea solo que sea `list`). Ojo: `bool` es subclase de `int`, así que `True` pasa como `int`.
- `Positivo` permite 0 (la consigna usa `default=0`) y rechaza negativos (`ValueError`) y no-números (`TypeError`).

## Qué se probó

Se corrieron los 15 scripts con `timeout` en Python 3.13; todos terminan con código 0 y la
salida coincide con la de la consigna: Fibonacci (0..34, 55, 89, límite 100), Timer en ambas
versiones (incluido con excepción), retry (aleatorio, determinístico que anda al 3er intento y
excepción no reintentable), chunked con range/str/lista vacía/generador infinito/archivo de 2500
líneas, pipeline (49, 121, 20, 10 y `['hello', 'world']` como decorador), Transaction (700 /
"Sin nombre"), BufferedReader comparado contra `splitlines()` con buffers de 1, 2, 3, 7, 64 y 8192
bytes, validate_types con todos los errores de la consigna, scheduler con el orden exacto del
ejemplo, singleton con 10 hilos (1 sola instancia) y Positivo con -50.

## Respuestas

**1.1 - ¿Qué pasa si hay una excepción dentro del `with`?** Con `@contextmanager`, la excepción
se relanza dentro del generador en el punto del `yield`. Como el `yield` está dentro de un
`try/finally`, el `finally` se ejecuta igual: cierra el archivo y lo borra. Después la excepción
sigue propagándose hacia afuera (no la tragamos). Probado en el `__main__`.

**1.3 - Lista vs generador. ¿Y si pido 10000 números?** Una función que retorna una lista calcula
y guarda *todos* los valores antes de devolver nada: memoria O(n) y tenés que saber de antemano
cuántos querés. El generador es lazy: calcula cada número recién cuando se lo pedís y solo guarda
el estado (`a`, `b`), así que usa memoria constante y puede ser infinito. Para 10000 números la
lista tendría 10000 enteros enormes en memoria (el último tiene 2090 dígitos); con el generador
podés recorrerlos o quedarte con el que necesitás (`islice`) sin guardarlos a todos. Además el
generador empieza a dar resultados enseguida.
