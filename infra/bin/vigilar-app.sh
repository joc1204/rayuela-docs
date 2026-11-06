#!/bin/bash
# Vigilante de una app: barato, sin tokens, avisa por Telegram.
#
#   vigilar-app.sh <servicio> <nombre visible> <puerto> [--probar]
#
# Que mira, cada 5 minutos:
#   1. que el servicio este activo
#   2. que /salud responda 200
#   3. errores nuevos en el log desde la ultima revision (Traceback, ERROR, Exception)
# Avisa SOLO si algo anda mal, con limite para no repetir el mismo aviso.
#
# Para asignar el aviso a otra persona: cambiar TELEGRAM_CHAT en /etc/rayuela/telegram.env.
# Para apagar el vigilante: crear el archivo /etc/rayuela/vigilante-off.
set -u

SERVICIO="${1:?falta el servicio}"
NOMBRE="${2:-$SERVICIO}"
PUERTO="${3:-}"
PROBAR="${4:-}"

BASE=/var/lib/rayuela-vigilante
mkdir -p "$BASE"
ESTADO="$BASE/$SERVICIO.estado"
ULTIMO_AVISO="$BASE/$SERVICIO.ultimo-aviso"

[ -f /etc/rayuela/vigilante-off ] && exit 0

avisar() {
  [ -x /usr/local/bin/avisar ] || return 0
  /usr/local/bin/avisar "🔎 $NOMBRE: $*" >/dev/null 2>&1
}

# permite probar el canal sin esperar un error real
if [ "$PROBAR" = "--probar" ]; then
  avisar "prueba del vigilante: el canal de avisos funciona"
  echo "prueba enviada"
  exit 0
fi

# --- 1. servicio activo
if ! systemctl is-active --quiet "$SERVICIO"; then
  avisar "el servicio NO esta activo (systemctl: $(systemctl is-active "$SERVICIO" 2>/dev/null))"
  exit 0
fi

# --- 2. responde /salud
if [ -n "$PUERTO" ]; then
  codigo=$(curl -s -o /dev/null -w '%{http_code}' --max-time 10 "http://127.0.0.1:$PUERTO/salud" 2>/dev/null)
  if [ "$codigo" != "200" ]; then
    avisar "no responde /salud en el puerto $PUERTO (codigo $codigo)"
  fi
fi

# --- 3. errores nuevos desde la ultima revision
DESDE=$(cat "$ESTADO" 2>/dev/null || echo '15 minutes ago')
AHORA=$(date '+%Y-%m-%d %H:%M:%S')
errores=$(journalctl -u "$SERVICIO" --since "$DESDE" --no-pager 2>/dev/null \
          | grep -icE "traceback|unhandled|ERROR in app|Exception on" || true)
echo "$AHORA" > "$ESTADO"

if [ "${errores:-0}" -gt 0 ]; then
  # firma del error para no repetir el mismo aviso
  firma=$(journalctl -u "$SERVICIO" --since "$DESDE" --no-pager 2>/dev/null \
          | grep -E "Traceback|Error|Exception" | tail -1 | md5sum | cut -c1-8)
  anterior=$(cat "$ULTIMO_AVISO" 2>/dev/null || echo '')
  ahora_epoch=$(date +%s)
  if [ "$firma" != "${anterior%%:*}" ] || [ $((ahora_epoch - ${anterior##*:} )) -gt 1800 ]; then
    detalle=$(journalctl -u "$SERVICIO" --since "$DESDE" --no-pager 2>/dev/null \
              | grep -E "Traceback|Error|Exception" | tail -2 | tr '\n' ' ' | cut -c1-220)
    avisar "$errores error(es) en el log: $detalle"
    echo "$firma:$ahora_epoch" > "$ULTIMO_AVISO"
  fi
fi

exit 0
