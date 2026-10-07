#!/usr/bin/env python3
"""
Adicional: crawler básico. Descarga una URL inicial, extrae sus enlaces y
descarga cada enlace con un pool de threads de tamaño limitado (Thread + Queue).

Uso: python3 ej12_crawler.py URL [-w WORKERS] [-m MAX_ENLACES]
"""
import argparse
import queue
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from html.parser import HTMLParser


class ExtractorEnlaces(HTMLParser):
    """Junta los href de las etiquetas <a>."""

    def __init__(self):
        super().__init__()
        self.enlaces = []

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            for nombre, valor in attrs:
                if nombre == "href" and valor:
                    self.enlaces.append(valor)


def descargar(url):
    with urllib.request.urlopen(url, timeout=10) as resp:
        return resp.read()


def extraer_enlaces(base, html):
    """Devuelve enlaces absolutos http(s), sin repetidos y sin #fragmentos."""
    parser = ExtractorEnlaces()
    parser.feed(html.decode("utf-8", errors="replace"))
    vistos = []
    for href in parser.enlaces:
        absoluto, _ = urllib.parse.urldefrag(urllib.parse.urljoin(base, href))
        if absoluto.startswith(("http://", "https://")) and absoluto not in vistos \
                and absoluto.rstrip("/") != base.rstrip("/"):
            vistos.append(absoluto)
    return vistos


def worker(cola, resultados, lock):
    while True:
        url = cola.get()
        if url is None:
            break
        inicio = time.time()
        try:
            datos = descargar(url)
            r = {"url": url, "ok": True, "bytes": len(datos)}
        except (urllib.error.URLError, OSError, ValueError) as e:
            r = {"url": url, "ok": False, "error": str(e)}
        r["tiempo"] = time.time() - inicio
        with lock:
            resultados.append(r)


def main():
    parser = argparse.ArgumentParser(description="Crawler básico de un nivel con pool de threads")
    parser.add_argument("url")
    parser.add_argument("-w", "--workers", type=int, default=4)
    parser.add_argument("-m", "--max", type=int, default=20, help="máximo de enlaces a seguir")
    args = parser.parse_args()

    try:
        html = descargar(args.url)
    except (urllib.error.URLError, OSError, ValueError) as e:
        print(f"No se pudo descargar la URL inicial: {e}")
        return
    enlaces = extraer_enlaces(args.url, html)[:args.max]
    print(f"{args.url}: {len(html):,} bytes, {len(enlaces)} enlaces a seguir con {args.workers} workers\n")

    cola = queue.Queue()
    resultados = []
    lock = threading.Lock()
    hilos = [threading.Thread(target=worker, args=(cola, resultados, lock)) for _ in range(args.workers)]
    for h in hilos:
        h.start()

    inicio = time.time()
    for e in enlaces:
        cola.put(e)
    for _ in hilos:
        cola.put(None)
    for h in hilos:
        h.join()

    for r in resultados:
        estado = f"{r['bytes']:>9,} bytes" if r["ok"] else f"ERROR: {r['error']}"
        print(f"  {r['url'][:60]:<60} {r['tiempo']:.2f}s  {estado}")
    ok = sum(r["ok"] for r in resultados)
    print(f"\n{ok}/{len(enlaces)} OK en {time.time() - inicio:.2f}s")


if __name__ == "__main__":
    main()
