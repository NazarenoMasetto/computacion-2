#!/usr/bin/env python3
"""Ejercicio 4.1 (+ 4.2): el gestor de tareas reescrito con Click.

Usa el mismo archivo ~/.tareas.json que tareas.py, así que son intercambiables.
Requiere: pip install click
"""
import json
import sys
from pathlib import Path

import click

ARCHIVO = Path.home() / ".tareas.json"
PRIORIDADES = click.Choice(["baja", "media", "alta"])


def cargar():
    if not ARCHIVO.exists():
        return {"siguiente_id": 1, "tareas": []}
    return json.loads(ARCHIVO.read_text(encoding="utf-8"))


def guardar(datos):
    ARCHIVO.write_text(json.dumps(datos, indent=2, ensure_ascii=False), encoding="utf-8")


def buscar(datos, id_tarea):
    for tarea in datos["tareas"]:
        if tarea["id"] == id_tarea:
            return tarea
    raise click.ClickException(f"no existe la tarea #{id_tarea}")


@click.group(help="Gestor de tareas simple (se guardan en ~/.tareas.json).")
def cli():
    pass


@cli.command(help="Agregar una tarea")
@click.argument("descripcion")
@click.option("--priority", type=PRIORIDADES, help="Prioridad de la tarea")
def add(descripcion, priority):
    datos = cargar()
    tarea = {"id": datos["siguiente_id"], "descripcion": descripcion,
             "prioridad": priority, "hecha": False}
    datos["tareas"].append(tarea)
    datos["siguiente_id"] += 1
    guardar(datos)
    extra = f" (prioridad: {priority})" if priority else ""
    click.echo(f"Tarea #{tarea['id']} agregada{extra}")


@cli.command(name="list", help="Listar tareas")
@click.option("--pending", is_flag=True, help="Solo pendientes")
@click.option("--done", is_flag=True, help="Solo completadas")
@click.option("--priority", type=PRIORIDADES, help="Filtrar por prioridad")
def listar(pending, done, priority):
    if pending and done:
        raise click.UsageError("--pending y --done son excluyentes")
    tareas = cargar()["tareas"]
    tareas = [t for t in tareas
              if (not pending or not t["hecha"]) and (not done or t["hecha"])
              and (not priority or t["prioridad"] == priority)]
    if not tareas:
        click.echo("No hay tareas para mostrar")
    for t in tareas:
        prio = f" [{t['prioridad'].upper()}]" if t["prioridad"] else ""
        click.echo(f"#{t['id']} [{'x' if t['hecha'] else ' '}] {t['descripcion']}{prio}")


@cli.command(help="Marcar una tarea como completada")
@click.argument("id_tarea", metavar="ID", type=int)
def done(id_tarea):
    datos = cargar()
    buscar(datos, id_tarea)["hecha"] = True
    guardar(datos)
    click.echo(f"Tarea #{id_tarea} completada")


@cli.command(help="Eliminar una tarea (pide confirmación)")
@click.argument("id_tarea", metavar="ID", type=int)
@click.option("-y", "--yes", is_flag=True, help="No pedir confirmación")
def remove(id_tarea, yes):
    datos = cargar()
    tarea = buscar(datos, id_tarea)
    if not yes:
        # click.confirm espera y/n; armamos el prompt en español con s/N
        respuesta = click.prompt(f'¿Eliminar "{tarea["descripcion"]}"? [s/N]',
                                 default="", show_default=False, prompt_suffix=" ")
        if respuesta.strip().lower() not in ("s", "si", "sí"):
            click.echo("Cancelado")
            return
    datos["tareas"].remove(tarea)
    guardar(datos)
    click.echo(f"Tarea #{id_tarea} eliminada")


if __name__ == "__main__":
    # prog_name fijo para que el autocompletado use la variable
    # _TAREAS_CLICK_COMPLETE (ver README, ejercicio 4.2)
    cli(prog_name="tareas-click")
