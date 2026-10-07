#!/usr/bin/env python3
"""Ej 2.3: send() vs sendall() con 10 MB.

send() devuelve cuántos bytes aceptó el kernel (puede ser menos de lo
pedido); sendall() insiste hasta mandar todo y devuelve None.

Uso:
    python3 ej2_send_vs_sendall.py [--port 8080] [--mb 10] [--timeout 2]

Levanta un receptor interno lento en ese puerto (no hace falta otra terminal).
"""
import argparse
import socket
import threading
import time


def receptor_lento(srv, total):
    """Acepta una conexión y lee despacio para que el buffer se llene."""
    conn, _ = srv.accept()
    with conn:
        time.sleep(0.5)       # mientras tanto el emisor ya hizo send()
        leidos = 0
        while leidos < total:
            pedazo = conn.recv(65536)
            if not pedazo:
                break
            leidos += len(pedazo)
    print(f'[receptor] leyó {leidos} bytes')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--port', type=int, default=8080)
    ap.add_argument('--mb', type=int, default=10)
    ap.add_argument('--timeout', type=float, default=0,
                    help='si > 0, el socket queda en modo timeout (no bloqueante '
                         'por dentro) y send() suele devolver menos')
    args = ap.parse_args()
    datos = b'x' * (args.mb * 1024 * 1024)

    srv = socket.socket()
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(('localhost', args.port))
    srv.listen(1)
    hilo = threading.Thread(target=receptor_lento, args=(srv, len(datos)))
    hilo.start()

    with socket.create_connection(('localhost', args.port)) as s:
        if args.timeout > 0:
            s.settimeout(args.timeout)
        enviados = s.send(datos)           # UNA sola llamada
        print(f'send() pidió {len(datos)} bytes y devolvió {enviados}')
        print(f'¿Mandó todo? {"sí" if enviados == len(datos) else "NO"}')
        resto = s.sendall(datos[enviados:])  # completar el resto
        print(f'sendall() del resto devolvió {resto!r} (None = mandó todo)')
    hilo.join()
    srv.close()


if __name__ == '__main__':
    main()
