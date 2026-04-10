import sys


def main():
    total = 0

    for argumento in sys.argv[1:]:
        try:
            total += float(argumento)
        except ValueError:
            print(f"Error: '{argumento}' no es un número válido.")
            sys.exit(1)

    print(f"Suma: {total}")


if __name__ == "__main__":
    main()