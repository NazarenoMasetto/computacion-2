def fibonacci(limite=None):
    a, b = 0, 1

    while True:
        if limite is not None and a > limite:
            break
        yield a
        a, b = b, a + b


if __name__ == "__main__":
    for numero in fibonacci(100):
        print(numero)