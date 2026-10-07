#!/usr/bin/env python3
"""Ejercicio 4.1: pipeline de dos comandos (equivalente a cmd1 | cmd2)."""
import os
import sys


def exec_o_morir(cmd, args):
    """Hace exec; si falla, avisa y termina el HIJO (no debe seguir el código del padre)."""
    try:
        os.execvp(cmd, [cmd] + args)
    except OSError as e:
        print(f"{cmd}: {e.strerror}", file=sys.stderr)
        os._exit(127)


def pipeline_dos_comandos(cmd1, args1, cmd2, args2):
    """Ejecuta cmd1 | cmd2 y devuelve los códigos de salida."""
    read_fd, write_fd = os.pipe()

    pid1 = os.fork()
    if pid1 == 0:
        os.close(read_fd)      # no lee
        os.dup2(write_fd, 1)   # stdout -> pipe
        os.close(write_fd)
        exec_o_morir(cmd1, args1)

    pid2 = os.fork()
    if pid2 == 0:
        os.close(write_fd)     # no escribe (si no lo cierra, nunca ve EOF)
        os.dup2(read_fd, 0)    # stdin <- pipe
        os.close(read_fd)
        exec_o_morir(cmd2, args2)

    # Padre: cerrar ambos extremos, si no el segundo comando se cuelga esperando EOF
    os.close(read_fd)
    os.close(write_fd)
    _, st1 = os.waitpid(pid1, 0)
    _, st2 = os.waitpid(pid2, 0)
    return os.waitstatus_to_exitcode(st1), os.waitstatus_to_exitcode(st2)


if __name__ == "__main__":
    print("=== ls -la | grep '.py' ===", flush=True)
    pipeline_dos_comandos("ls", ["-la"], "grep", [".py"])
