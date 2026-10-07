import argparse
import secrets
import string


def main():
    parser = argparse.ArgumentParser(description="Genera contraseñas aleatorias.")
    parser.add_argument("-n", "--length", type=int, default=12, help="Longitud")
    parser.add_argument("--no-symbols", action="store_true", help="Sin símbolos")
    parser.add_argument("--no-numbers", action="store_true", help="Sin números")
    parser.add_argument("--count", type=int, default=1, help="Cantidad de contraseñas")
    args = parser.parse_args()

    caracteres = string.ascii_letters

    if not args.no_numbers:
        caracteres += string.digits

    if not args.no_symbols:
        caracteres += "!@#$%&"

    for _ in range(args.count):
        password = "".join(secrets.choice(caracteres) for _ in range(args.length))
        print(password)


if __name__ == "__main__":
    main()