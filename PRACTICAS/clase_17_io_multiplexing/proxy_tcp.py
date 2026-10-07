#!/usr/bin/env python3
"""Adicional: proxy TCP con selectors.

Escucha en --port (default 8080) y reenvía cada conexión a --destino
host:puerto, en los dos sentidos. Por cada cliente hay DOS sockets
relacionados (cliente <-> destino); el selector vigila ambos y cada uno
sabe quién es su "par".

Para no bloquear, lo que llega de un lado se encola en un buffer del otro
y se manda cuando el selector avisa EVENT_WRITE. Cuando un lado cierra su
escritura (EOF), se le pasa el cierre al otro con shutdown(SHUT_WR) recién
después de vaciar el buffer, así no se pierden datos en vuelo.

Uso:
    python3 proxy_tcp.py --destino localhost:9000 [--port 8080]
"""
import argparse
import selectors
import socket

sel = selectors.DefaultSelector()
par = {}            # socket -> el socket del otro lado
salida = {}         # socket -> bytes pendientes para escribirle
eof = set()         # sockets de los que ya leímos EOF
registrados = set() # sockets que están hoy en el selector


def actualizar_eventos(sock):
    """Vigilar lectura mientras no haya EOF, y escritura si hay pendiente."""
    eventos = 0
    if sock not in eof:
        eventos |= selectors.EVENT_READ
    if salida[sock]:
        eventos |= selectors.EVENT_WRITE
    if eventos and sock in registrados:
        sel.modify(sock, eventos)
    elif eventos:
        sel.register(sock, eventos)
        registrados.add(sock)
    elif sock in registrados:
        # Nada que vigilar (EOF y sin pendientes): sale del selector, pero
        # sigue en el túnel hasta que el otro lado termine.
        sel.unregister(sock)
        registrados.discard(sock)


def cerrar_par(sock):
    """Cierra los dos extremos de un túnel."""
    for s in (sock, par.get(sock)):
        if s is None or s not in par:
            continue
        if s in registrados:
            sel.unregister(s)
            registrados.discard(s)
        par.pop(s, None)
        salida.pop(s, None)
        eof.discard(s)
        s.close()
    print('- túnel cerrado', flush=True)


def tal_vez_terminar(sock):
    """Si los dos lados mandaron EOF y no queda nada por enviar, cerrar."""
    otro = par[sock]
    if {sock, otro} <= eof and not salida[sock] and not salida[otro]:
        cerrar_par(sock)
        return True
    return False


def aceptar(servidor, destino):
    cliente, direccion = servidor.accept()
    try:
        remoto = socket.create_connection(destino, timeout=5)
    except OSError as e:
        print(f'no se pudo conectar a {destino}: {e}', flush=True)
        cliente.close()
        return
    for s in (cliente, remoto):
        s.setblocking(False)
        sel.register(s, selectors.EVENT_READ)
        registrados.add(s)
        salida[s] = b''
    par[cliente], par[remoto] = remoto, cliente
    print(f'+ túnel {direccion} <-> {destino}', flush=True)


def leer(sock):
    otro = par[sock]
    try:
        datos = sock.recv(65536)
    except ConnectionResetError:
        cerrar_par(sock)
        return
    if datos:
        salida[otro] += datos           # lo que llega de un lado va al otro
        actualizar_eventos(otro)
        return
    # EOF: este lado no manda más
    eof.add(sock)
    if not salida[otro]:
        otro.shutdown(socket.SHUT_WR)   # pasarle el EOF al otro lado
    if not tal_vez_terminar(sock):
        actualizar_eventos(sock)


def escribir(sock):
    try:
        n = sock.send(salida[sock])
    except (BrokenPipeError, ConnectionResetError):
        cerrar_par(sock)
        return
    salida[sock] = salida[sock][n:]
    if not salida[sock] and par[sock] in eof:
        sock.shutdown(socket.SHUT_WR)   # buffer vaciado: ahora sí el EOF
    if not tal_vez_terminar(sock):
        actualizar_eventos(sock)


def main():
    parser = argparse.ArgumentParser(description='Proxy TCP con selectors')
    parser.add_argument('--port', type=int, default=8080)
    parser.add_argument('--destino', required=True, help='host:puerto')
    args = parser.parse_args()
    host, puerto = args.destino.rsplit(':', 1)
    destino = (host, int(puerto))

    servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    servidor.bind(('0.0.0.0', args.port))
    servidor.listen(128)
    servidor.setblocking(False)
    sel.register(servidor, selectors.EVENT_READ)
    print(f'Proxy :{args.port} -> {host}:{puerto}', flush=True)

    try:
        while True:
            for clave, mascara in sel.select():
                sock = clave.fileobj
                if sock is servidor:
                    aceptar(servidor, destino)
                    continue
                # Puede haberse cerrado antes en esta misma tanda de eventos
                if sock not in par:
                    continue
                if mascara & selectors.EVENT_READ:
                    leer(sock)
                if mascara & selectors.EVENT_WRITE and sock in par:
                    escribir(sock)
    except KeyboardInterrupt:
        print('\nProxy detenido')
    finally:
        sel.close()


if __name__ == '__main__':
    main()
