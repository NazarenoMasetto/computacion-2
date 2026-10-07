#!/usr/bin/env python3
"""
Ejercicio 9 (obligatorio): descargador paralelo con un pool FIJO de threads
hecho a mano con threading.Thread + queue.Queue. Maneja errores de red y muestra estadísticas.

Uso: python3 ej9_descargador.py [-w WORKERS] [URL ...]
Sin URLs usa la lista de ejemplo de la consigna.
"""
import argparse
import queue
import threading
import time
import urllib.error
import urllib.request

URLS_EJEMPLO = [
    "https://www.python.org",
    "https://docs.python.org",
    "https://pypi.org",
    "https://www.google.com",
    "https://www.github.com",
]


def worker(in_q, out_list, lock):
    """Saca URLs de la cola hasta recibir None; guarda el resultado (ok o error)."""
    nombre = threading.current_thread().name
    while True:
        url = in_q.get()
        if url is None:
            in_q.task_done()
            break
        inicio = time.time()
        try:
            with urllib.request.urlopen(url, timeout=10) as response:
                datos = response.read()
            registro = {"url": url, "ok": True, "bytes": len(datos)}
        except (urllib.error.URLError, OSError, ValueError) as e:
            # URLError cubre HTTPError, DNS, conexión rechazada; OSError timeouts; ValueError URLs mal formadas
            registro = {"url": url, "ok": False, "error": str(e)}
        registro["tiempo"] = time.time() - inicio
        registro["worker"] = nombre
        with lock:
            out_list.append(registro)
        in_q.task_done()


def main():
    parser = argparse.ArgumentParser(description="Descargador paralelo con pool de threads")
    parser.add_argument("urls", nargs="*", default=URLS_EJEMPLO)
    parser.add_argument("-w", "--workers", type=int, default=4)
    args = parser.parse_args()

    in_q = queue.Queue()
    resultados = []
    lock = threading.Lock()

    # Pool fijo: se crean NUM_WORKERS hilos, no uno por URL
    workers = [threading.Thread(target=worker, args=(in_q, resultados, lock), name=f"W{i}")
               for i in range(args.workers)]
    for w in workers:
        w.start()

    inicio = time.time()
    for url in args.urls:
        in_q.put(url)
    # Señales de fin (una por worker)
    for _ in workers:
        in_q.put(None)
    for w in workers:
        w.join()
    tiempo_total = time.time() - inicio

    # Estadísticas
    print(f"{'URL':<45}{'Worker':>7}{'Estado':>8}{'Bytes':>10}{'Tiempo':>8}")
    for r in resultados:
        estado = "OK" if r["ok"] else "ERROR"
        print(f"{r['url'][:44]:<45}{r['worker']:>7}{estado:>8}{r.get('bytes', 0):>10,}{r['tiempo']:>7.2f}s")
        if not r["ok"]:
            print(f"    -> {r['error']}")

    ok = sum(1 for r in resultados if r["ok"])
    bytes_total = sum(r.get("bytes", 0) for r in resultados)
    suma_tiempos = sum(r["tiempo"] for r in resultados)
    print(f"\nDescargas exitosas: {ok}/{len(args.urls)}")
    print(f"Errores: {len(args.urls) - ok}")
    print(f"Bytes totales: {bytes_total:,}")
    print(f"Tiempo total: {tiempo_total:.2f}s (suma de tiempos individuales: {suma_tiempos:.2f}s)")


if __name__ == "__main__":
    main()
