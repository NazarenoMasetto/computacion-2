"""Corre las tres mediciones obligatorias contra la API ya levantada.

Uso (con `docker compose up` corriendo en otra terminal):
    python3 mediciones.py                  # las tres
    python3 mediciones.py --solo 3         # una sola

Las mediciones 1 y 2 se repiten varias veces (--repeticiones, default 3) y se
reporta la mediana, para que un valor suelto (una red lenta en ese momento,
el arranque en frío de las conexiones) no distorsione el resultado.

Los datos crudos de cada corrida se guardan en resultados/ como JSON.

Solo usa la biblioteca estándar, no hace falta instalar nada.
"""
import argparse
import json
import statistics
import time
import urllib.request
from pathlib import Path

API = "http://localhost:8000"

# 20 URLs reales y livianas para la medición 1.
URLS = [
    "https://www.python.org", "https://docs.python.org/3/",
    "https://pypi.org", "https://github.com", "https://www.wikipedia.org",
    "https://es.wikipedia.org", "https://www.um.edu.ar", "https://example.com",
    "https://www.debian.org", "https://ubuntu.com", "https://www.kernel.org",
    "https://fastapi.tiangolo.com", "https://www.python-httpx.org",
    "https://docs.docker.com", "https://www.mozilla.org", "https://www.gnu.org",
    "https://www.w3.org", "https://www.iana.org", "https://www.rust-lang.org",
    "https://go.dev",
]


# ------------------------------------------------------------ helpers HTTP

def _pedir(metodo: str, ruta: str, cuerpo: dict | None = None):
    datos = json.dumps(cuerpo).encode() if cuerpo is not None else None
    req = urllib.request.Request(API + ruta, data=datos, method=metodo,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as resp:
        return json.loads(resp.read())


def crear(tipo: str, parametros: dict, timeout: float = 300) -> str:
    return _pedir("POST", "/tareas",
                  {"tipo": tipo, "parametros": parametros, "timeout": timeout})["id"]


def esperar_fin(ids: list[str]) -> list[dict]:
    """Consulta cada 50 ms hasta que todas las tareas terminen."""
    while True:
        tareas = [_pedir("GET", f"/tareas/{i}") for i in ids]
        if all(t["estado"] in ("completada", "fallida", "cancelada") for t in tareas):
            return tareas
        time.sleep(0.05)


def latencia_get() -> float:
    inicio = time.perf_counter()
    _pedir("GET", "/tareas")
    return time.perf_counter() - inicio


def titulo(texto: str) -> None:
    print(f"\n{'=' * 64}\n{texto}\n{'=' * 64}")


def ms(segundos: float) -> str:
    return f"{segundos * 1000:.1f}"


# ------------------------------------------------------------ medición 1

def _una_descarga(urls: list[str], concurrente: bool) -> dict:
    tarea = esperar_fin([crear("descargar",
                               {"urls": urls, "concurrente": concurrente})])[0]
    if tarea["estado"] != "completada":
        raise SystemExit(f"La descarga terminó en {tarea['estado']}: {tarea['error']}")
    r = tarea["resultado"]
    filas = r["resultados"]
    lenta = max(filas, key=lambda f: f["segundos"])
    return {
        "total": r["total_segundos"],
        "ok": sum(1 for f in filas if "status" in f),
        "mas_lenta_s": lenta["segundos"],
        "mas_lenta_url": lenta["url"],
        "suma_s": round(sum(f["segundos"] for f in filas), 3),
        "errores": [f for f in filas if "error" in f],
    }


def medicion_1(urls: list[str], reps: int) -> dict:
    titulo(f"MEDICIÓN 1 · {len(urls)} descargas: secuencial vs concurrente "
           f"({reps} repeticiones)")
    corridas: dict[str, list[dict]] = {"secuencial": [], "concurrente": []}
    for i in range(reps):
        # Se alternan los modos en cada repetición para que ninguno quede
        # siempre primero (el primero paga el arranque en frío de la red).
        for modo, concurrente in (("secuencial", False), ("concurrente", True)):
            c = _una_descarga(urls, concurrente)
            corridas[modo].append(c)
            print(f"  corrida {i + 1} {modo:<12} {c['total']:7.3f} s   "
                  f"(ok {c['ok']}/{len(urls)}, más lenta {c['mas_lenta_s']:.3f} s "
                  f"= {c['mas_lenta_url']})")

    med = {m: statistics.median(c["total"] for c in v) for m, v in corridas.items()}
    print(f"\n  Mediana secuencial:  {med['secuencial']:7.3f} s")
    print(f"  Mediana concurrente: {med['concurrente']:7.3f} s")
    print(f"  Speedup (medianas):  {med['secuencial'] / med['concurrente']:.1f}x")
    for c in corridas["secuencial"] + corridas["concurrente"]:
        for e in c["errores"]:
            print(f"  ⚠ {e['url']}: {e['error']}")
    return {"urls": urls, "corridas": corridas, "medianas": med,
            "speedup": med["secuencial"] / med["concurrente"]}


# ------------------------------------------------------------ medición 2

def _gets_durante(tid: str) -> list[float]:
    # Pide GET /tareas, uno detrás del otro, mientras la tarea siga viva.
    latencias = []
    while True:
        latencias.append(latencia_get())
        if _pedir("GET", f"/tareas/{tid}")["estado"] not in ("pendiente", "ejecutando"):
            return latencias
        time.sleep(0.1)


def medicion_2(iteraciones: int, reps: int) -> dict:
    titulo(f"MEDICIÓN 2 · GET /tareas durante un hash de {iteraciones:,} "
           f"iteraciones ({reps} repeticiones)")
    reposo = [latencia_get() for _ in range(20)]
    print(f"  En reposo: mediana {ms(statistics.median(reposo))} ms (20 GETs)")

    resultado = {"iteraciones": iteraciones, "reposo_s": reposo}
    for etiqueta, bloqueante in (("sin_executor", True), ("con_executor", False)):
        corridas = []
        for i in range(reps):
            tid = crear("hashear", {"texto": "computacion2",
                                    "iteraciones": iteraciones,
                                    "bloqueante": bloqueante})
            time.sleep(0.2)   # dar tiempo a que un worker la tome
            lat = _gets_durante(tid)
            hash_s = esperar_fin([tid])[0]["resultado"]["segundos"]
            corridas.append({"latencias_s": lat, "hash_s": hash_s})
            print(f"  {etiqueta} corrida {i + 1}: {len(lat):3d} GETs   "
                  f"prom {ms(statistics.mean(lat)):>7} ms   "
                  f"máx {ms(max(lat)):>7} ms   (hash {hash_s:.2f} s)")
        resultado[etiqueta] = corridas

    print()
    for etiqueta in ("sin_executor", "con_executor"):
        c = resultado[etiqueta]
        print(f"  {etiqueta:<13} mediana de promedios "
              f"{ms(statistics.median(statistics.mean(x['latencias_s']) for x in c)):>7} ms"
              f"   mediana de máximos "
              f"{ms(statistics.median(max(x['latencias_s']) for x in c)):>7} ms"
              f"   GETs {statistics.median(len(x['latencias_s']) for x in c):.0f}"
              f"   hash {statistics.median(x['hash_s'] for x in c):.2f} s")
    return resultado


# ------------------------------------------------------------ medición 3

def _lote(tipo: str, parametros: dict, n: int) -> float:
    inicio = time.perf_counter()
    esperar_fin([crear(tipo, parametros) for _ in range(n)])
    return time.perf_counter() - inicio


def medicion_3(niveles: list[int], iteraciones: int) -> dict:
    workers = _pedir("GET", "/estadisticas")["workers"]
    titulo(f"MEDICIÓN 3 · Techo del pool ({workers} workers)")
    resultado = {"workers": workers, "esperar": [], "hashear": []}

    print("  a) Tareas I/O: 'esperar' de 1 s cada una")
    print(f"     {'N':>5} {'total (s)':>10} {'tareas/s':>9}")
    for n in niveles:
        total = _lote("esperar", {"segundos": 1}, n)
        resultado["esperar"].append({"n": n, "total_s": total})
        print(f"     {n:>5} {total:>10.2f} {n / total:>9.2f}")

    print(f"\n  b) Tareas CPU: 'hashear' de {iteraciones:,} iteraciones (con executor)")
    print(f"     {'N':>5} {'total (s)':>10} {'s/tarea':>9}")
    for n in [x for x in niveles if x <= 16]:
        total = _lote("hashear", {"texto": "x", "iteraciones": iteraciones}, n)
        resultado["hashear"].append({"n": n, "total_s": total})
        print(f"     {n:>5} {total:>10.2f} {total / n:>9.2f}")
    return resultado


# ------------------------------------------------------------ main

def main() -> None:
    global API
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--api", default=API)
    p.add_argument("--solo", type=int, choices=[1, 2, 3], help="correr una sola")
    p.add_argument("--repeticiones", type=int, default=3,
                   help="repeticiones de las mediciones 1 y 2 (default 3)")
    p.add_argument("--hash-pesado", type=int, default=5_000_000,
                   help="iteraciones para la medición 2 (default 5M)")
    p.add_argument("--hash-liviano", type=int, default=1_000_000,
                   help="iteraciones por tarea en la medición 3 (default 1M)")
    p.add_argument("--niveles", default="1,2,4,8,16,32,64")
    p.add_argument("--urls", help="archivo con una URL por línea (opcional)")
    a = p.parse_args()
    API = a.api.rstrip("/")

    urls = URLS
    if a.urls:
        with open(a.urls) as f:
            urls = [linea.strip() for linea in f if linea.strip()]

    try:
        _pedir("GET", "/estadisticas")
    except OSError as e:
        raise SystemExit(f"No puedo conectarme a {API} ({e}). "
                         "¿Está corriendo docker compose up?")

    datos = {"fecha": time.strftime("%Y-%m-%d %H:%M:%S")}
    if a.solo in (None, 1):
        datos["medicion_1"] = medicion_1(urls, a.repeticiones)
    if a.solo in (None, 2):
        datos["medicion_2"] = medicion_2(a.hash_pesado, a.repeticiones)
    if a.solo in (None, 3):
        datos["medicion_3"] = medicion_3([int(x) for x in a.niveles.split(",")],
                                         a.hash_liviano)

    carpeta = Path(__file__).parent / "resultados"
    carpeta.mkdir(exist_ok=True)
    archivo = carpeta / f"mediciones_{time.strftime('%Y%m%d_%H%M%S')}.json"
    archivo.write_text(json.dumps(datos, indent=2, ensure_ascii=False))
    print(f"\nDatos crudos guardados en {archivo}\n")


if __name__ == "__main__":
    main()
