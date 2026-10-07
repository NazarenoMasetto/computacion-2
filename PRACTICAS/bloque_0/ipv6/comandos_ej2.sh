#!/usr/bin/env bash
# Uso: bash comandos_ej2.sh [interfaz]   (default eth0)
# Ejercicio 2: las direcciones IPv6 de tu máquina. Solo lee información;
# no cambia nada del sistema. Cada comando puede fallar si la máquina no
# tiene IPv6 (o no tiene 'ip'/'ping6'): se avisa y se sigue.
cd "$(dirname "$0")"
corre() { echo; echo "\$ $*"; "$@" || echo "   (falló con código $?)"; }

# Antes de empezar: ¿hay direcciones? ¿hay ruta a Internet?
corre ip -6 addr show
corre ping6 -c2 -W2 2001:4860:4860::8888

# 1-2. Contar direcciones por scope y cuántas interfaces tienen fe80::
echo; echo "== Direcciones por scope"
ip -6 addr show 2>/dev/null | awk '/inet6/ {print $4}' | sort | uniq -c
echo "== Interfaces con link-local (fe80::)"
ip -6 addr show scope link 2>/dev/null | grep -c 'inet6 fe80' || true

# 3. Dirección global y ruta, por separado (secciones 3 y 6 del explorador)
corre ip -6 route show default
# explorar_ipv6.py es el archivo de la cátedra (bloque_0_autonomo/ipv6/).
# Pasale la ruta con: EXPLORAR=/ruta/a/explorar_ipv6.py bash comandos_ej2.sh
EXPLORAR=${EXPLORAR:-explorar_ipv6.py}
if [[ -f "$EXPLORAR" ]]; then
    corre python3 "$EXPLORAR"
else
    echo "   (no encuentro $EXPLORAR; definí EXPLORAR con su ruta)"
fi

# 5. Ping a link-local SIN interfaz: falla porque es ambiguo
corre ping6 -c1 -W1 fe80::1
# 6. Con la interfaz (cambiá eth0 por la tuya, ver 'ip -6 addr')
IFAZ=${1:-eth0}
corre ping6 -c1 -W1 "fe80::1%$IFAZ"

# 7-8. getsockname() con IPv6
corre python3 ej2_getsockname.py
