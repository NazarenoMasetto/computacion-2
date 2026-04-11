def pipeline(*funciones):
    def ejecutar(valor):
        resultado = valor
        for funcion in funciones:
            resultado = funcion(resultado)
        return resultado
    return ejecutar


def doble(x):
    return x * 2


def sumar_uno(x):
    return x + 1


def cuadrado(x):
    return x ** 2


if __name__ == "__main__":
    p = pipeline(doble, sumar_uno, cuadrado)
    print(p(3))
    print(p(5))