# Código del ejercicio 2.2 (se corre dentro de un contenedor en la red redis-net,
# después de "pip install redis").
import redis

r = redis.Redis(host='redis', port=6379)
r.set('nombre', 'Docker')
r.set('contador', 0)
r.incr('contador')
r.incr('contador')
print(f"Nombre: {r.get('nombre').decode()}")
print(f"Contador: {r.get('contador').decode()}")
