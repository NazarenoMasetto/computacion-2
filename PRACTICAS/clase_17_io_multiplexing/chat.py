#!/usr/bin/env python3
"""Ejercicio 6: chat multiusuario con selectors, extendido.

Sobre el chat.py de la clase se agregan:
  - /nick <nombre>  cambiar el apodo
  - /lista          ver quiénes están conectados
  - framing correcto: un buffer de entrada por cliente, que acumula bytes
    y solo procesa líneas COMPLETAS (como framing.py de la clase 13)

Uso:
    python3 chat.py [--port 8080]
    nc localhost 8080       (desde varias terminales)
"""
import argparse
import selectors
import socket

sel = selectors.DefaultSelector()
clientes = {}           # socket -> apodo
salida = {}             # socket -> bytes pendientes de enviar
entrada = {}            # socket -> bytes recibidos que todavía no son línea
MAX_LINEA = 4096        # una "línea" más larga que esto se descarta


def encolar(conn, mensaje: bytes):
    """Agrega a la cola de salida de un cliente y pide aviso de escritura."""
    salida[conn] = salida.get(conn, b'') + mensaje
    sel.modify(conn, selectors.EVENT_READ | selectors.EVENT_WRITE, manejar)


def difundir(mensaje: bytes, excepto=None):
    """Encola (no escribe directo) para todos menos uno."""
    for conn in clientes:
        if conn is not excepto:
            encolar(conn, mensaje)


def aceptar(servidor, _mascara):
    conn, direccion = servidor.accept()
    conn.setblocking(False)
    apodo = f'{direccion[0]}:{direccion[1]}'
    clientes[conn] = apodo
    entrada[conn] = b''
    sel.register(conn, selectors.EVENT_READ, manejar)
    print(f'+ {apodo}  ({len(clientes)} conectados)', flush=True)
    encolar(conn, b'Bienvenido al chat. Comandos: /nick <nombre>, /lista\n')
    difundir(f'* se conecto {apodo}\n'.encode(), excepto=conn)


def desconectar(conn):
    apodo = clientes.pop(conn, '?')
    salida.pop(conn, None)
    entrada.pop(conn, None)
    sel.unregister(conn)            # SIEMPRE antes de close()
    conn.close()
    print(f'- {apodo}  ({len(clientes)} conectados)', flush=True)
    difundir(f'* se fue {apodo}\n'.encode())


def procesar_linea(conn, texto):
    """Una línea completa de un cliente: comando o mensaje al chat."""
    apodo = clientes[conn]
    if texto.startswith('/nick'):
        partes = texto.split(maxsplit=1)
        if len(partes) < 2:
            encolar(conn, b'Uso: /nick <nombre>\n')
            return
        nuevo = partes[1].strip()
        if nuevo in clientes.values():
            encolar(conn, f'El apodo {nuevo} ya esta en uso\n'.encode())
            return
        clientes[conn] = nuevo
        encolar(conn, f'Ahora sos {nuevo}\n'.encode())
        difundir(f'* {apodo} ahora es {nuevo}\n'.encode(), excepto=conn)
    elif texto == '/lista':
        nombres = ', '.join(sorted(clientes.values()))
        encolar(conn, f'{len(clientes)} conectados: {nombres}\n'.encode())
    elif texto:
        print(f'  <{apodo}> {texto}', flush=True)
        difundir(f'<{apodo}> {texto}\n'.encode(), excepto=conn)


def manejar(conn, mascara):
    if mascara & selectors.EVENT_READ:
        try:
            datos = conn.recv(4096)
        except ConnectionResetError:
            datos = b''
        if not datos:
            desconectar(conn)
            return
        # Framing: recv() puede traer media línea o varias juntas.
        # Acumulamos y cortamos solo por '\n'; el resto queda para después.
        entrada[conn] += datos
        while b'\n' in entrada[conn]:
            linea, entrada[conn] = entrada[conn].split(b'\n', 1)
            procesar_linea(conn, linea.decode('utf-8', 'replace').rstrip('\r'))
        if len(entrada[conn]) > MAX_LINEA:
            entrada[conn] = b''         # cliente que nunca manda '\n'
            encolar(conn, b'Linea demasiado larga, descartada\n')

    if mascara & selectors.EVENT_WRITE and conn in clientes:
        buf = salida.get(conn, b'')
        if buf:
            try:
                n = conn.send(buf)
            except (BrokenPipeError, ConnectionResetError):
                desconectar(conn)
                return
            salida[conn] = buf[n:]
        if not salida.get(conn):
            sel.modify(conn, selectors.EVENT_READ, manejar)


def main():
    parser = argparse.ArgumentParser(description='Chat con selectors')
    parser.add_argument('--port', type=int, default=8080)
    args = parser.parse_args()

    servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    servidor.bind(('0.0.0.0', args.port))
    servidor.listen(128)
    servidor.setblocking(False)
    sel.register(servidor, selectors.EVENT_READ, aceptar)
    print(f'Chat escuchando en :{args.port} ({type(sel).__name__})', flush=True)

    try:
        while True:
            for clave, mascara in sel.select():
                clave.data(clave.fileobj, mascara)
    except KeyboardInterrupt:
        print('\nChat detenido')
    finally:
        sel.close()


if __name__ == '__main__':
    main()
