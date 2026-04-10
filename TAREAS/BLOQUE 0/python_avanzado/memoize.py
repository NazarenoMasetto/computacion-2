from functools import wraps


def memoize(funcion):
    cache = {}
    hits = 0
    misses = 0

    @wraps(funcion)
    def wrapper(*args):
        nonlocal hits, misses

        if args in cache:
            hits += 1
            return cache[args]

        misses += 1
        resultado = funcion(*args)
        cache[args] = resultado
        return resultado

    wrapper.cache = cache

    def cache_info():
        return {
            "hits": hits,
            "misses": misses,
            "size": len(cache)
        }

    def clear_cache():
        nonlocal hits, misses
        cache.clear()
        hits = 0
        misses = 0

    wrapper.cache_info = cache_info
    wrapper.clear_cache = clear_cache
    return wrapper


@memoize
def fibonacci(n):
    if n < 2:
        return n
    return fibonacci(n - 1) + fibonacci(n - 2)


if __name__ == "__main__":
    print(fibonacci(10))
    print(fibonacci.cache_info())