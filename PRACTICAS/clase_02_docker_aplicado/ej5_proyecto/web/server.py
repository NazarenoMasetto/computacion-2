"""Servicio web del proyecto integrador.

Servidor HTTP simple (http.server de la stdlib) que responde con información
del sistema y el valor actual del contador que incrementa el worker en Redis.

Variables de entorno:
    REDIS_HOST  host de Redis (default: localhost)
    PORT        puerto donde escucha (default: 8000)
"""

import json
import os
import platform
import socket
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer

import redis

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
PORT = int(os.getenv("PORT", "8000"))

r = redis.Redis(host=REDIS_HOST, port=6379, decode_responses=True)


class Manejador(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/":
            # Cada visita también se cuenta en Redis
            try:
                visitas = r.incr("visitas_web")
                contador = r.get("contador")
                ultimo = r.get("worker_ultimo")
                redis_ok = True
            except redis.RedisError:
                visitas = contador = ultimo = None
                redis_ok = False

            datos = {
                "servicio": "web",
                "hostname": socket.gethostname(),
                "python": platform.python_version(),
                "sistema": f"{platform.system()} {platform.release()}",
                "cpus": os.cpu_count(),
                "hora": datetime.now().isoformat(timespec="seconds"),
                "redis_ok": redis_ok,
                "contador_worker": int(contador) if contador else 0,
                "worker_ultimo_tick": ultimo,
                "visitas_web": visitas,
            }
            self.responder(200, datos)
        elif self.path == "/health":
            self.responder(200, {"ok": True})
        else:
            self.responder(404, {"error": "no encontrado"})

    def responder(self, codigo, datos):
        cuerpo = json.dumps(datos, indent=2, ensure_ascii=False).encode()
        self.send_response(codigo)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(cuerpo)))
        self.end_headers()
        self.wfile.write(cuerpo)


if __name__ == "__main__":
    servidor = HTTPServer(("0.0.0.0", PORT), Manejador)
    print(f"Web escuchando en el puerto {PORT} (Redis en {REDIS_HOST})", flush=True)
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        pass
