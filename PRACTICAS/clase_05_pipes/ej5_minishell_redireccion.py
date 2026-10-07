#!/usr/bin/env python3
"""Ejercicio 5 (obligatorio): mini-shell con redirección.

Soporta: comandos externos, exit, cd, `>` (truncar), `>>` (append) y `<` (entrada).
"""
import os
import shlex
import sys


def parsear_linea(linea):
    """
    Parsea una línea de comando.
    Retorna (comando, args, archivo_salida, archivo_entrada, append)

    Ejemplos:
      "ls -la"        -> ("ls", ["-la"], None, None, False)
      "ls > out.txt"  -> ("ls", [], "out.txt", None, False)
      "ls >> out.txt" -> ("ls", [], "out.txt", None, True)
      "cat < in.txt"  -> ("cat", [], None, "in.txt", False)
    Lanza ValueError si falta el nombre de archivo después de > / >> / <.
    """
    partes = shlex.split(linea)  # respeta comillas: echo "hola mundo"
    comando = None
    args = []
    archivo_salida = None
    archivo_entrada = None
    append = False

    i = 0
    while i < len(partes):
        token = partes[i]
        if token in (">", ">>", "<"):
            if i + 1 >= len(partes):
                raise ValueError(f"falta el archivo después de '{token}'")
            if token == "<":
                archivo_entrada = partes[i + 1]
            else:
                archivo_salida = partes[i + 1]
                append = token == ">>"
            i += 2
            continue
        if comando is None:
            comando = token
        else:
            args.append(token)
        i += 1

    return comando, args, archivo_salida, archivo_entrada, append


def ejecutar(comando, args, archivo_salida=None, archivo_entrada=None, append=False):
    """Ejecuta un comando con redirección opcional. Devuelve el código de salida."""
    pid = os.fork()

    if pid == 0:
        # Las redirecciones se arman en el HIJO, antes del exec
        try:
            if archivo_salida:
                modo = os.O_APPEND if append else os.O_TRUNC
                fd = os.open(archivo_salida, os.O_CREAT | os.O_WRONLY | modo, 0o644)
                os.dup2(fd, 1)  # stdout -> archivo
                os.close(fd)
            if archivo_entrada:
                fd = os.open(archivo_entrada, os.O_RDONLY)
                os.dup2(fd, 0)  # stdin <- archivo
                os.close(fd)
        except OSError as e:
            print(f"minish: {e.filename}: {e.strerror}", file=sys.stderr)
            os._exit(1)

        try:
            os.execvp(comando, [comando] + args)
        except OSError as e:
            print(f"minish: {comando}: {e.strerror}", file=sys.stderr)
            os._exit(127)

    _, status = os.waitpid(pid, 0)
    return os.waitstatus_to_exitcode(status)


def main():
    while True:
        try:
            linea = input("minish$ ")
        except EOFError:
            print("\nChau!")
            break

        linea = linea.strip()
        if not linea:
            continue

        try:
            comando, args, salida, entrada, append = parsear_linea(linea)
        except ValueError as e:
            print(f"minish: error de sintaxis: {e}")
            continue

        if comando == "exit":
            break
        if comando == "cd":  # interno: tiene que cambiar el directorio del shell mismo
            try:
                os.chdir(args[0] if args else os.environ.get("HOME", "/"))
            except OSError as e:
                print(f"cd: {e.strerror}")
            continue

        if comando:
            codigo = ejecutar(comando, args, salida, entrada, append)
            if codigo != 0:
                print(f"[código {codigo}]")


if __name__ == "__main__":
    main()
