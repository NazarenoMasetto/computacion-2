#!/usr/bin/env python3
"""Ejercicio 4.2: pipeline de tres comandos (cmd1 | cmd2 | cmd3)."""
import os
import sys


def exec_o_morir(cmd, args):
    """Hace exec; si falla, termina el hijo con 127."""
    try:
        os.execvp(cmd, [cmd] + args)
    except OSError as e:
        print(f"{cmd}: {e.strerror}", file=sys.stderr)
        os._exit(127)


def pipeline_tres_comandos(cmd1, args1, cmd2, args2, cmd3, args3):
    """Ejecuta cmd1 | cmd2 | cmd3"""
    pipe1_read, pipe1_write = os.pipe()
    pipe2_read, pipe2_write = os.pipe()

    # cmd1: stdout -> pipe1
    pid1 = os.fork()
    if pid1 == 0:
        os.close(pipe1_read)
        os.close(pipe2_read)
        os.close(pipe2_write)
        os.dup2(pipe1_write, 1)
        os.close(pipe1_write)
        exec_o_morir(cmd1, args1)

    # cmd2: stdin <- pipe1, stdout -> pipe2
    pid2 = os.fork()
    if pid2 == 0:
        os.close(pipe1_write)
        os.close(pipe2_read)
        os.dup2(pipe1_read, 0)
        os.dup2(pipe2_write, 1)
        os.close(pipe1_read)
        os.close(pipe2_write)
        exec_o_morir(cmd2, args2)

    # cmd3: stdin <- pipe2
    pid3 = os.fork()
    if pid3 == 0:
        os.close(pipe1_read)
        os.close(pipe1_write)
        os.close(pipe2_write)
        os.dup2(pipe2_read, 0)
        os.close(pipe2_read)
        exec_o_morir(cmd3, args3)

    # Padre: cerrar TODOS los extremos y esperar
    for fd in (pipe1_read, pipe1_write, pipe2_read, pipe2_write):
        os.close(fd)
    for pid in (pid1, pid2, pid3):
        os.waitpid(pid, 0)


if __name__ == "__main__":
    print("=== cat /etc/passwd | grep root | wc -l ===", flush=True)
    pipeline_tres_comandos("cat", ["/etc/passwd"], "grep", ["root"], "wc", ["-l"])
