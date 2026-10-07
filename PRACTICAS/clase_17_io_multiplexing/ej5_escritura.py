#!/usr/bin/env python3
"""Ejercicio 5: escritura no bloqueante con buffer + EVENT_WRITE.

Basado en servidor_selectors.py de la clase. Con --write-siempre se
registra EVENT_WRITE de forma permanente (el error del 5.2) para ver el
consumo de CPU: un socket casi siempre está "listo para escribir", así que
select() vuelve enseguida una y otra vez.

Uso:
    python3 ej5_escritura.py [--port 8080]
    python3 ej5_escritura.py --write-siempre [--port 8080]
"""
import argparse
import selectors
import socket

sel = selectors.DefaultSelector()
pendiente = {}          # socket -> bytes que faltan enviar
WRITE_SIEMPRE = False
vueltas = 0             # cuántos eventos procesó el loop


def aceptar(servidor, _mascara):
    conn, direccion = servidor.accept()
    conn.setblocking(False)
    eventos = selectors.EVENT_READ
    if WRITE_SIEMPRE:
        eventos |= selectors.EVENT_WRITE     # el error: nunca se saca
    sel.register(conn, eventos, manejar)
    print(f'+ cliente {direccion}', flush=True)


def cerrar(conn):
    sel.unregister(conn)
    pendiente.pop(conn, None)
    conn.close()
    print('- cliente', flush=True)


def manejar(conn, mascara):
    if mascara & selectors.EVENT_READ:
        try:
            datos = conn.recv(4096)
        except ConnectionResetError:
            datos = b''
        if not datos:
            cerrar(conn)
            return
        pendiente[conn] = pendiente.get(conn, b'') + datos
        # Ahora sí interesa saber cuándo se puede escribir
        sel.modify(conn, selectors.EVENT_READ | selectors.EVENT_WRITE, manejar)

    if mascara & selectors.EVENT_WRITE:
        buf = pendiente.get(conn, b'')
        if buf:
            try:
                n = conn.send(buf)       # send(): lo que entre, sin bloquear
            except (BrokenPipeError, ConnectionResetError):
                cerrar(conn)
                return
            pendiente[conn] = buf[n:]
        if not pendiente.get(conn) and not WRITE_SIEMPRE:
            sel.modify(conn, selectors.EVENT_READ, manejar)


def main():
    global WRITE_SIEMPRE, vueltas
    parser = argparse.ArgumentParser(description='Escritura no bloqueante')
    parser.add_argument('--port', type=int, default=8080)
    parser.add_argument('--write-siempre', action='store_true')
    args = parser.parse_args()
    WRITE_SIEMPRE = args.write_siempre

    servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    servidor.bind(('0.0.0.0', args.port))
    servidor.listen(128)
    servidor.setblocking(False)
    sel.register(servidor, selectors.EVENT_READ, aceptar)
    print(f'Escuchando en :{args.port} (write_siempre={WRITE_SIEMPRE})', flush=True)

    try:
        while True:
            for clave, mascara in sel.select():
                vueltas += 1
                clave.data(clave.fileobj, mascara)
    except KeyboardInterrupt:
        print(f'\nServidor detenido. Eventos procesados: {vueltas}')
    finally:
        sel.close()


if __name__ == '__main__':
    main()
