#!/usr/bin/env python3
"""Ej 3 partes B, C y D: retransmisión, duplicados y números de secuencia.

Servidor: pasa a mayúsculas y CUENTA cuántas veces hizo el trabajo real.
Cliente: manda N mensajes reintentando, y al final pregunta el contador.

Uso:
    python3 ej3_confiable.py servidor [--port 8080] [--perdida 0.3] [--protocolo simple|seq] [--demora 0]
    python3 ej3_confiable.py cliente  [--port 8080] [--perdida 0.3] [--protocolo simple|seq]
                                      [--n 20] [--timeout 0.5] [--intentos 5]

--protocolo simple  sin números de secuencia (partes B y C: el servidor procesa de más)
--protocolo seq     [4 bytes seq][payload]: el servidor deduplica (parte D)
--perdida           probabilidad de descartar cada datagrama al enviarlo (ambos lados)
--demora            el servidor tarda esto en responder (provoca respuestas viejas)
"""
import argparse
import random
import socket
import struct
import time

STATS = b'\x00STATS'     # mensaje de control: nunca se "pierde"


def empaquetar(seq, payload):
    return struct.pack('!I', seq) + payload      # '!' = orden de red


def desempaquetar(datos):
    (seq,) = struct.unpack('!I', datos[:4])
    return seq, datos[4:]


def enviar(sock, datos, destino, prob):
    """sendto() que simula la red: a veces no manda y no avisa."""
    if random.random() >= prob:
        sock.sendto(datos, destino)


# ------------------------------------------------------------------ servidor

def servidor(args):
    trabajos = 0
    vistos = {}       # (origen, seq) -> respuesta ya calculada
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(('0.0.0.0', args.port))
        print(f'[servidor {args.protocolo}] puerto {args.port} pérdida={args.perdida}',
              flush=True)
        while True:
            datos, origen = s.recvfrom(65535)
            if datos == STATS:
                s.sendto(str(trabajos).encode(), origen)
                continue
            if args.demora:
                time.sleep(args.demora)
            if args.protocolo == 'simple':
                trabajos += 1                         # trabajo real, SIEMPRE
                enviar(s, datos.upper(), origen, args.perdida)
                continue
            seq, payload = desempaquetar(datos)
            clave = (origen, seq)
            if clave in vistos:
                respuesta = vistos[clave]             # duplicado: NO rehacer
                print(f'  dup seq={seq} de {origen[1]}: reenvío guardada', flush=True)
            else:
                trabajos += 1
                respuesta = payload.upper()
                vistos[clave] = respuesta
            enviar(s, empaquetar(seq, respuesta), origen, args.perdida)


# ------------------------------------------------------------------ cliente

def pedir_con_reintentos(sock, mensaje, destino, intentos=5, timeout=0.5, prob=0.0):
    """Manda y reintenta si no llega respuesta. Devuelve (respuesta|None, intentos)."""
    sock.settimeout(timeout)
    for intento in range(1, intentos + 1):
        enviar(sock, mensaje, destino, prob)
        try:
            datos, _ = sock.recvfrom(65535)
            return datos, intento
        except TimeoutError:
            continue
    return None, intentos


def pedir_con_seq(sock, seq, payload, destino, intentos=5, timeout=0.5, prob=0.0):
    """Igual, pero descarta respuestas cuyo seq no sea el del pedido en curso."""
    sock.settimeout(timeout)
    descartadas = 0
    for intento in range(1, intentos + 1):
        enviar(sock, empaquetar(seq, payload), destino, prob)
        limite = time.monotonic() + timeout
        while (resto := limite - time.monotonic()) > 0:
            sock.settimeout(resto)
            try:
                datos, _ = sock.recvfrom(65535)
            except TimeoutError:
                break
            seq_resp, respuesta = desempaquetar(datos)
            if seq_resp == seq:
                return respuesta, intento, descartadas
            descartadas += 1          # respuesta vieja de un intento anterior
    return None, intentos, descartadas


def consultar_trabajos(sock, destino):
    """Pregunta al servidor su contador (mensaje de control, sin pérdidas)."""
    sock.settimeout(1.0)
    for _ in range(3):
        sock.sendto(STATS, destino)
        try:
            while True:
                datos, _ = sock.recvfrom(65535)
                if datos.isdigit():
                    return int(datos)
        except TimeoutError:
            continue
    return None


def cliente(args):
    destino = ('localhost', args.port)
    total_intentos = ok = mal = fallidos = descartadas = 0
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        antes = consultar_trabajos(s, destino)
        for i in range(args.n):
            payload = f'mensaje {i}'.encode()
            if args.protocolo == 'simple':
                resp, intentos = pedir_con_reintentos(
                    s, payload, destino, args.intentos, args.timeout, args.perdida)
            else:
                resp, intentos, desc = pedir_con_seq(
                    s, i, payload, destino, args.intentos, args.timeout, args.perdida)
                descartadas += desc
            total_intentos += intentos
            if resp is None:
                fallidos += 1
            elif resp == payload.upper():
                ok += 1
            else:
                mal += 1          # contestó otra cosa: respuesta vieja tomada como nueva
        time.sleep(max(args.timeout, 0.3))   # que lleguen los rezagados
        despues = consultar_trabajos(s, destino)

    print(f'Protocolo {args.protocolo}, pérdida {args.perdida:.0%} por sentido, '
          f'timeout {args.timeout}s')
    print(f'  Mensajes: {args.n}  OK: {ok}  respuesta INCORRECTA: {mal}  sin respuesta: {fallidos}')
    print(f'  Envíos reales: {total_intentos} (promedio {total_intentos / args.n:.2f} por mensaje)')
    if args.protocolo == 'seq':
        print(f'  Respuestas viejas descartadas por seq: {descartadas}')
    if antes is not None and despues is not None:
        print(f'  Veces que el servidor hizo el trabajo: {despues - antes}')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('rol', choices=['servidor', 'cliente'])
    ap.add_argument('--port', type=int, default=8080)
    ap.add_argument('--perdida', type=float, default=0.3)
    ap.add_argument('--protocolo', choices=['simple', 'seq'], default='seq')
    ap.add_argument('--demora', type=float, default=0.0)
    ap.add_argument('--n', type=int, default=20)
    ap.add_argument('--timeout', type=float, default=0.5)
    ap.add_argument('--intentos', type=int, default=5)
    args = ap.parse_args()
    if args.rol == 'servidor':
        servidor(args)
    else:
        cliente(args)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('\nCortado')
