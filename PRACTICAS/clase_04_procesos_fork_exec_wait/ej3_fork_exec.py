#!/usr/bin/env python3
"""Ejercicio 3: mini-launcher con el patrón fork + exec + wait.

Uso: python3 ej3_fork_exec.py [comando [args...]]   (por defecto: ls -la /tmp)
"""
import os
import sys


def lanzar(comando, args):
    """Ejecuta comando en un hijo y devuelve su código de salida."""
    pid = os.fork()
    if pid == 0:
        try:
            os.execvp(comando, [comando] + args)
        except OSError as e:
            # Si exec vuelve es porque falló
            print(f"Error: no se pudo ejecutar {comando}: {e}", file=sys.stderr)
            os._exit(127)
    _, status = os.waitpid(pid, 0)
    if os.WIFSIGNALED(status):
        return 128 + os.WTERMSIG(status)
    return os.WEXITSTATUS(status)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        cmd, argumentos = sys.argv[1], sys.argv[2:]
    else:
        cmd, argumentos = "ls", ["-la", "/tmp"]
    codigo = lanzar(cmd, argumentos)
    print(f"Comando '{cmd}' terminó con código {codigo}")
