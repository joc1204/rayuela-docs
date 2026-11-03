#!/bin/bash
# verificar_netbook.sh — Chequeo de salud del servidor domotica-bangho.
#
# SOLO LECTURA: no reinicia servicios, no toca configuración, no publica nada.
# Lo único que escribe es un HTML temporal en /tmp, y lo borra al salir.
#
# Por qué el chequeo externo usa la IP pública del relay y no el nombre:
#   desde la propia netbook, MagicDNS resuelve net-casa... a la IP interna, así
#   que curl devuelve 200 aunque el túnel esté roto (trampa 3 del documento
#   SERVIDOR-DESPLIEGUE-Y-TUNEL.md). Acá se resuelve el nombre contra 8.8.8.8
#   y se fuerza esa IP con --resolve, que es un chequeo honesto.
#
# Además compara los puestos de /etc/tunel-apps.conf contra los que el relay
# realmente publica (trampa 5: el vigilante cuenta las líneas del archivo, no
# lo que el plano de control de Tailscale conoce).
#
# Uso:
#   bash verificar_netbook.sh            # chequeo completo
#   bash verificar_netbook.sh --local    # sin chequeo externo (si no hay internet)
#
# Código de salida: 0 = todo bien · 1 = alguna falla.

set -u

CONF=/etc/tunel-apps.conf
TMP=/tmp/.verificar_netbook.html
EXTERNO=1
[ "${1:-}" = "--local" ] && EXTERNO=0

OK=0; FAIL=0; WARN=0
ok()    { OK=$((OK+1));     printf '  [ OK  ] %s\n' "$*"; }
falla() { FAIL=$((FAIL+1)); printf '  [FALLA] %s\n' "$*"; }
aviso() { WARN=$((WARN+1)); printf '  [AVISO] %s\n' "$*"; }
seccion() { printf '\n=== %s ===\n' "$*"; }

trap 'rm -f "$TMP"' EXIT

# ---------------------------------------------------------------- 1. entorno
seccion "1. Red y entorno"

printf '  hostname: %s\n' "$(hostname)"
printf '  uptime:   %s\n' "$(uptime | sed 's/^ *//')"

IP_LAN=$(hostname -I | tr ' ' '\n' | grep -E '^192\.168\.|^10\.|^172\.(1[6-9]|2[0-9]|3[01])\.' | head -1)
IP_TS=$(hostname -I | tr ' ' '\n' | grep -E '^100\.' | head -1)
[ -n "$IP_LAN" ] && ok "IP de la LAN: $IP_LAN" || aviso "no detecté IP de LAN"
[ -n "$IP_TS" ]  && ok "IP de Tailscale: $IP_TS" || aviso "no detecté IP de Tailscale (¿tailscaled caído?)"
printf '  gateway:  %s\n' "$(ip route | awk '/^default/{print $3; exit}')"

USO_DISCO=$(df -h / | awk 'NR==2{gsub("%","",$5); print $5}')
MEM_LIBRE=$(free -m | awk '/^Mem:/{print $7}')
if [ "${USO_DISCO:-100}" -ge 90 ]; then falla "disco al ${USO_DISCO}%"; else ok "disco al ${USO_DISCO}%"; fi
if [ "${MEM_LIBRE:-0}" -lt 80 ]; then aviso "memoria disponible baja: ${MEM_LIBRE} MB"; else ok "memoria disponible: ${MEM_LIBRE} MB"; fi

# ------------------------------------------------------------- 2. tailscale
seccion "2. Tailscale y Funnel"

if systemctl is-active --quiet tailscaled; then ok "tailscaled activo"; else falla "tailscaled NO está activo"; fi

HOST=""
if command -v tailscale >/dev/null 2>&1; then
  ESTADO_TS=$(tailscale status 2>&1 | head -1)
  printf '  status: %s\n' "$ESTADO_TS"
  FUNNEL=$(tailscale funnel status 2>/dev/null)
  if [ -z "$FUNNEL" ]; then
    falla "no pude leer 'tailscale funnel status' (¿permisos?)"
  else
    HOST=$(printf '%s\n' "$FUNNEL" | grep -oE 'https://[a-zA-Z0-9.-]+' | head -1 | sed 's|https://||')
    [ -n "$HOST" ] && ok "host público del funnel: $HOST" || falla "el funnel no tiene host público"
  fi
else
  falla "no está el comando tailscale"
fi

# ---------------------------------------------- 3. puestos: archivo vs relay
seccion "3. Puestos publicados (archivo vs relay)"

PATHS=(); DESTS=()
if [ -r "$CONF" ]; then
  while read -r p d; do
    case "${p:-}" in ''|'#'*) continue ;; esac
    PATHS+=("$p"); DESTS+=("${d:-}")
  done < "$CONF"
  ok "leí $CONF (${#PATHS[@]} puestos)"
else
  falla "no puedo leer $CONF"
fi

if [ "${#PATHS[@]}" -gt 0 ] && [ -n "${FUNNEL:-}" ]; then
  PUBLICADOS=$(printf '%s\n' "$FUNNEL" | sed -n 's/^|-- \([^ ]*\).*/\1/p')
  for p in "${PATHS[@]}"; do
    if printf '%s\n' "$PUBLICADOS" | grep -qxF "$p"; then
      ok "el relay publica $p"
    else
      falla "el relay NO publica $p (está en el archivo pero no en el plano de control)"
    fi
  done
fi

# ------------------------------------------------------------- 4. servicios
seccion "4. Servicios"

for s in gastos.service presupuestito.service rayuela-novedades.service funnel-check.timer; do
  if systemctl is-active --quiet "$s"; then ok "$s activo"; else falla "$s NO está activo"; fi
done

PROX=$(systemctl list-timers funnel-check.timer --no-pager 2>/dev/null | sed -n '2p' | awk '{print $1, $2, $3, $4, $5, $6}')
[ -n "$PROX" ] && printf '  próximo vigilante: %s\n' "$PROX"

if ps aux | grep -q '[n]ode-red'; then
  ok "Node-RED corriendo ($(ps -o user= -C node-red 2>/dev/null | head -1 | tr -d ' ' || echo '?'))"
else
  falla "Node-RED NO está corriendo"
fi

# ---------------------------------------------------------------- 5. puertos
seccion "5. Puertos de las apps"

puerto_de() {
  case "$1" in
    *127.0.0.1:*) printf '%s' "$1" | sed -n 's|.*127\.0\.0\.1:\([0-9]\+\).*|\1|p' ;;
    [0-9]*)       printf '%s' "$1" | sed -n 's|^\([0-9]\+\).*|\1|p' ;;
    *)            printf '' ;;
  esac
}

if [ "${#DESTS[@]}" -gt 0 ]; then
  for i in "${!DESTS[@]}"; do
    puerto=$(puerto_de "${DESTS[$i]}")
    [ -z "$puerto" ] && continue
    if ss -tln 2>/dev/null | grep -qE "[:.]$puerto[[:space:]]"; then
      ok "puerto $puerto escuchando (${PATHS[$i]})"
    else
      falla "puerto $puerto NO escucha (${PATHS[$i]})"
    fi
  done
fi

# ------------------------------------------------- 6. verificación externa
seccion "6. Verificación externa real (IP pública, sin MagicDNS)"

if [ "$EXTERNO" -eq 0 ]; then
  aviso "salteada por --local"
elif [ -z "$HOST" ]; then
  falla "sin host público no puedo verificar desde afuera"
else
  PUBIP=$(dig +short "$HOST" @8.8.8.8 2>/dev/null | grep -E '^[0-9.]+$' | tail -1)
  if [ -z "$PUBIP" ]; then
    PUBIP=$(getent ahostsv4 "$HOST" 2>/dev/null | awk 'NR==1{print $1}')
  fi
  if [ -z "$PUBIP" ]; then
    falla "no pude resolver la IP pública de $HOST"
  else
    printf '  IP pública del relay: %s\n' "$PUBIP"
    for i in "${!PATHS[@]}"; do
      p="${PATHS[$i]}"
      # Algunos puestos son sólo un prefijo, sin página propia (ej. /app).
      # Para no dar un falso negativo se sondea una página real adentro.
      sonda="$p"; esperado=""
      case "$p" in
        /app)            sonda="/app/pendientes"; esperado="Pendientes" ;;
        /app/pendientes) esperado="Pendientes" ;;
        /app/pedido)     esperado="Pedido" ;;
        /app/catalogo)   esperado="Catálogo" ;;
        /gastos)         esperado="Cuenta Clara" ;;
        /presupuestos)   esperado="Presupuestito" ;;
        /ferias)         esperado="Rayuela" ;;
        /novedades)      esperado="Novedades" ;;
      esac
      code=$(curl -s -o "$TMP" -w '%{http_code}' -L --max-time 25 \
             --resolve "$HOST:443:$PUBIP" "https://$HOST$sonda" 2>/dev/null)
      titulo=$(grep -oiE '<title>[^<]*</title>' "$TMP" 2>/dev/null | head -1 | sed -E 's|</?title>||Ig')
      etiqueta="$p"; [ "$sonda" != "$p" ] && etiqueta="$p (sonda $sonda)"
      if [ "$code" = "200" ]; then
        if [ -n "$esperado" ] && ! printf '%s' "$titulo" | grep -qiF "$esperado"; then
          aviso "$etiqueta responde 200 pero el título no es el esperado (dice: '${titulo:-sin título}')"
        else
          ok "$etiqueta → 200 · ${titulo:-sin título}"
        fi
      elif [ "$code" = "404" ] && [ -z "$titulo" ]; then
        falla "$etiqueta → 404 del relay (el plano de control no conoce la ruta)"
      elif [ "$code" = "404" ]; then
        aviso "$etiqueta → 404 de la app (el relay la conoce, la app no tiene página ahí)"
      else
        falla "$etiqueta → HTTP $code · ${titulo:-sin título}"
      fi
    done
  fi
fi

# ------------------------------------ 7. sanity de la API de la Mini App
seccion "7. API de la Mini App (validación de Telegram)"

code=$(curl -s -o /dev/null -w '%{http_code}' --max-time 8 "http://127.0.0.1:1880/app/api/pendientes" 2>/dev/null)
case "$code" in
  401) ok "endpoint sin firma devuelve 401 (existe y valida)" ;;
  404) falla "el endpoint /app/api/pendientes no existe (¿falta deploy?)" ;;
  *)   aviso "respuesta inesperada del endpoint: HTTP $code" ;;
esac

# ---------------------------------------------------------------- resumen
seccion "Resumen"
printf '  OK: %d · AVISOS: %d · FALLAS: %d\n' "$OK" "$WARN" "$FAIL"
if [ "$FAIL" -gt 0 ]; then
  echo "  RESULTADO: HAY FALLAS"
  exit 1
fi
echo "  RESULTADO: todo en orden"
exit 0
