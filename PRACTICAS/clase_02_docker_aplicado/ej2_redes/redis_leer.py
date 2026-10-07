# Tarea 2.2: desde un contenedor NUEVO, leer lo que quedó en Redis
# (sin volver a setear nada) para ver si los datos persisten.
import redis

r = redis.Redis(host='redis', port=6379)
nombre = r.get('nombre')
contador = r.get('contador')
print(f"Nombre: {nombre.decode() if nombre else None}")
print(f"Contador: {contador.decode() if contador else None}")
