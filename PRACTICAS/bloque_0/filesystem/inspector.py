import argparse
import os
import stat
import pwd
import grp
from datetime import datetime


def tipo_archivo(ruta):
    if os.path.islink(ruta):
        return "enlace simbólico"
    if os.path.isdir(ruta):
        return "directorio"
    if os.path.isfile(ruta):
        return "archivo regular"
    if stat.S_ISCHR(os.lstat(ruta).st_mode):
        return "dispositivo de caracteres"
    if stat.S_ISBLK(os.lstat(ruta).st_mode):
        return "dispositivo de bloques"
    return "otro"


def permisos_texto(modo):
    return stat.filemode(modo)


def permisos_octal(modo):
    return oct(modo & 0o777)


def formatear_fecha(timestamp):
    return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")


def cantidad_elementos_directorio(ruta):
    try:
        return len(os.listdir(ruta))
    except OSError:
        return "no disponible"


def main():
    parser = argparse.ArgumentParser(
        description="Muestra información detallada de un archivo o directorio."
    )
    parser.add_argument("ruta", help="Ruta del archivo o directorio")
    args = parser.parse_args()

    ruta = args.ruta

    if not os.path.exists(ruta) and not os.path.islink(ruta):
        print(f"Error: la ruta '{ruta}' no existe.")
        return

    try:
        info = os.lstat(ruta)
    except OSError:
        print(f"Error: no se pudo acceder a '{ruta}'.")
        return

    print(f"Archivo: {ruta}")
    print(f"Tipo: {tipo_archivo(ruta)}")
    print(f"Tamaño: {info.st_size} bytes")
    print(f"Permisos: {permisos_texto(info.st_mode)} ({permisos_octal(info.st_mode)})")

    try:
        usuario = pwd.getpwuid(info.st_uid).pw_name
    except KeyError:
        usuario = str(info.st_uid)

    try:
        grupo = grp.getgrgid(info.st_gid).gr_name
    except KeyError:
        grupo = str(info.st_gid)

    print(f"Propietario: {usuario} (uid: {info.st_uid})")
    print(f"Grupo: {grupo} (gid: {info.st_gid})")
    print(f"Inodo: {info.st_ino}")
    print(f"Enlaces duros: {info.st_nlink}")
    print(f"Último acceso: {formatear_fecha(info.st_atime)}")
    print(f"Última modificación: {formatear_fecha(info.st_mtime)}")
    print(f"Último cambio: {formatear_fecha(info.st_ctime)}")

    if os.path.islink(ruta):
        try:
            destino = os.readlink(ruta)
            print(f"Apunta a: {destino}")
        except OSError:
            print("Apunta a: no disponible")

    if os.path.isdir(ruta):
        print(f"Contenido: {cantidad_elementos_directorio(ruta)} elementos")


if __name__ == "__main__":
    main()