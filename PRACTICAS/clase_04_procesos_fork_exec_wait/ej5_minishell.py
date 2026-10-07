#!/usr/bin/env python3
"""Ejercicio 5 (obligatorio): mini-shell con fork + exec + wait.

Soporta: exit, cd (interno), comandos externos y muestra el código si no es 0.
Extra: export VAR=valor y procesos en background con '&'.
"""
import os
import shlex
import sys


def ejecutar(partes, background=False):
    """Hace fork+exec del comando. Si es background no espera al hijo."""
    pid = os.fork()
    if pid == 0:
        try:
            os.execvp(partes[0], partes)
        except OSError as e:
            print(f"{partes[0]}: {e.strerror}", file=sys.stderr)
            os._exit(127)

    if background:
        print(f"[background] PID {pid}")
        return

    _, status = os.waitpid(pid, 0)
    if os.WIFEXITED(status):
        codigo = os.WEXITSTATUS(status)
        if codigo != 0:
            print(f"[Salió con código {codigo}]")
    elif os.WIFSIGNALED(status):
        print(f"[Terminado por señal {os.WTERMSIG(status)}]")


def recoger_background():
    """Recoge hijos en background que ya terminaron (para no dejar zombies)."""
    while True:
        try:
            pid, status = os.waitpid(-1, os.WNOHANG)
        except ChildProcessError:
            return
        if pid == 0:
            return
        print(f"[background] PID {pid} terminó con código {os.waitstatus_to_exitcode(status)}")


def shell():
    while True:
        recoger_background()
        try:
            linea = input("$ ")
        except EOFError:
            print()
            break

        try:
            partes = shlex.split(linea)  # respeta comillas
        except ValueError as e:
            print(f"Error de sintaxis: {e}")
            continue
        if not partes:
            continue

        comando = partes[0]

        # Comandos internos: se ejecutan en el propio shell, sin fork
        if comando == "exit":
            break
        if comando == "cd":
            destino = partes[1] if len(partes) > 1 else os.environ.get("HOME", "/")
            try:
                os.chdir(destino)
            except OSError as e:
                print(f"cd: {e.strerror}: {destino}")
            continue
        if comando == "export":
            for asignacion in partes[1:]:
                if "=" in asignacion:
                    clave, valor = asignacion.split("=", 1)
                    os.environ[clave] = valor  # los hijos lo heredan
            continue

        background = partes[-1] == "&"
        if background:
            partes = partes[:-1]
            if not partes:
                continue

        ejecutar(partes, background)


if __name__ == "__main__":
    shell()
