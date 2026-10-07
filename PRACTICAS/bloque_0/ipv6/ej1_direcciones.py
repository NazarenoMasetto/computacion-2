#!/usr/bin/env python3
"""Ejercicio 1: verificar con ipaddress la compresión/expansión hecha a mano."""
import ipaddress

# 1.1: (original, lo que comprimí a mano)
COMPRIMIR = [
    ("2001:0db8:0000:0000:0000:ff00:0042:8329", "2001:db8::ff00:42:8329"),
    ("0000:0000:0000:0000:0000:0000:0000:0001", "::1"),
    ("fe80:0000:0000:0000:0202:b3ff:fe1e:8329", "fe80::202:b3ff:fe1e:8329"),
    ("2001:0db8:0000:0000:0001:0000:0000:0001", "2001:db8::1:0:0:1"),
]

# 1.2: (comprimida, lo que expandí a mano)
EXPANDIR = [
    ("::1", "0000:0000:0000:0000:0000:0000:0000:0001"),
    ("2001:db8::8a2e:370:7334", "2001:0db8:0000:0000:0000:8a2e:0370:7334"),
    ("ff02::1", "ff02:0000:0000:0000:0000:0000:0000:0001"),
]


def verificar(titulo, pares, atributo):
    print(f"\n== {titulo}")
    for original, a_mano in pares:
        real = getattr(ipaddress.ip_address(original), atributo)
        estado = "OK" if real == a_mano else f"MAL (era {real})"
        print(f"  {original:<41} -> {a_mano:<41} {estado}")


def ambiguedad():
    """Ejercicio 1.1 punto 5: '::' dos veces es ambiguo."""
    print("\n== 5. ¿Por qué no puede haber dos '::'?")
    texto = "2001:db8::1::1"
    try:
        ipaddress.ip_address(texto)
    except ValueError as e:
        print(f"  ipaddress rechaza '{texto}': {e}")
    # Hay 4 grupos escritos, faltan 4 grupos de ceros para llegar a 8,
    # y no se sabe cómo repartirlos entre los dos '::'.
    print("  Interpretaciones posibles (entre otras):")
    for antes in range(1, 4):
        despues = 4 - antes
        grupos = ["2001", "db8"] + ["0"] * antes + ["1"] + ["0"] * despues + ["1"]
        dir_ = ipaddress.ip_address(":".join(grupos))
        print(f"    {antes} grupo(s) en el 1er '::' y {despues} en el 2do -> "
              f"{dir_.exploded}")


def clasificar():
    """Ejercicio 1.3: los flags se solapan (ver preguntas 9 y 10)."""
    print("\n== Flags de la stdlib")
    for texto in ["2001:db8::1", "ff02::1"]:
        a = ipaddress.ip_address(texto)
        print(f"  {texto:<12} is_global={a.is_global} is_private={a.is_private} "
              f"is_multicast={a.is_multicast} is_reserved={a.is_reserved}")


if __name__ == "__main__":
    verificar("1.1 Compresión (.compressed)", COMPRIMIR, "compressed")
    verificar("1.2 Expansión (.exploded)", EXPANDIR, "exploded")
    ambiguedad()
    clasificar()
