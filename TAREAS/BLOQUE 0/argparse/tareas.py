import argparse
import json
import os


ARCHIVO_TAREAS = "tareas.json"


def cargar_tareas():
    if not os.path.exists(ARCHIVO_TAREAS):
        return []

    try:
        with open(ARCHIVO_TAREAS, "r", encoding="utf-8") as archivo:
            return json.load(archivo)
    except (json.JSONDecodeError, OSError):
        return []


def guardar_tareas(tareas):
    with open(ARCHIVO_TAREAS, "w", encoding="utf-8") as archivo:
        json.dump(tareas, archivo, indent=4, ensure_ascii=False)


def agregar_tarea(descripcion):
    tareas = cargar_tareas()
    nueva = {
        "id": len(tareas) + 1,
        "descripcion": descripcion,
        "completada": False
    }
    tareas.append(nueva)
    guardar_tareas(tareas)
    print("Tarea agregada.")


def listar_tareas(solo_pendientes=False):
    tareas = cargar_tareas()

    if not tareas:
        print("No hay tareas.")
        return

    for tarea in tareas:
        if solo_pendientes and tarea["completada"]:
            continue

        estado = "✔" if tarea["completada"] else "✘"
        print(f'{tarea["id"]}. [{estado}] {tarea["descripcion"]}')


def completar_tarea(tarea_id):
    tareas = cargar_tareas()

    for tarea in tareas:
        if tarea["id"] == tarea_id:
            tarea["completada"] = True
            guardar_tareas(tareas)
            print("Tarea completada.")
            return

    print("No se encontró la tarea.")


def eliminar_tarea(tarea_id):
    tareas = cargar_tareas()
    nuevas_tareas = [t for t in tareas if t["id"] != tarea_id]

    if len(nuevas_tareas) == len(tareas):
        print("No se encontró la tarea.")
        return

    for i, tarea in enumerate(nuevas_tareas, start=1):
        tarea["id"] = i

    guardar_tareas(nuevas_tareas)
    print("Tarea eliminada.")


def main():
    parser = argparse.ArgumentParser(description="Administrador simple de tareas.")
    subparsers = parser.add_subparsers(dest="comando")

    parser_agregar = subparsers.add_parser("agregar", help="Agregar una tarea")
    parser_agregar.add_argument("descripcion", help="Descripción de la tarea")

    parser_listar = subparsers.add_parser("listar", help="Listar tareas")
    parser_listar.add_argument(
        "--pendientes",
        action="store_true",
        help="Mostrar solo tareas pendientes"
    )

    parser_completar = subparsers.add_parser("completar", help="Marcar tarea como completada")
    parser_completar.add_argument("id", type=int, help="ID de la tarea")

    parser_eliminar = subparsers.add_parser("eliminar", help="Eliminar una tarea")
    parser_eliminar.add_argument("id", type=int, help="ID de la tarea")

    args = parser.parse_args()

    if args.comando == "agregar":
        agregar_tarea(args.descripcion)
    elif args.comando == "listar":
        listar_tareas(args.pendientes)
    elif args.comando == "completar":
        completar_tarea(args.id)
    elif args.comando == "eliminar":
        eliminar_tarea(args.id)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()