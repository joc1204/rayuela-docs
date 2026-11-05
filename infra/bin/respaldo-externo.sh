#!/bin/bash
# Arma el paquete externo cifrado: catalogo + fichas + configuracion del VPS.
# No incluye tapas (se pueden re-scrapear) ni secretos (/etc/rayuela/*.env).
# Salida: /var/backups/rayuela/externo/rayuela-<fecha>.tar.gz.gpg
set -u
DEST=/var/backups/rayuela/externo
FECHA=$(date +%Y-%m-%d)
PASSFILE=/root/.respaldo-pass
LOG=$DEST/respaldo-externo.log

mkdir -p "$DEST"
TMP=$(mktemp -d /tmp/respaldo-externo-XXXXXX)

echo "$(date '+%F %T') armando paquete" >> "$LOG"

# 1) copia consistente del catalogo
if ! sqlite3 /opt/rayuela/demo/catalogo.db ".backup '$TMP/catalogo.db'"; then
  echo "$(date '+%F %T') FALLA: no pude copiar el catalogo" >> "$LOG"
  rm -rf "$TMP"
  exit 1
fi

# 2) ultima configuracion del respaldo diario (unidades, nginx, scripts; sin secretos)
ULTIMA_CONFIG=$(ls -t /var/backups/rayuela/config-*.tar.gz 2>/dev/null | head -1)
[ -n "$ULTIMA_CONFIG" ] && cp "$ULTIMA_CONFIG" "$TMP/config.tar.gz"

# 3) paquete comprimido y cifrado
SALIDA="$DEST/rayuela-$FECHA.tar.gz.gpg"
if tar czf - -C "$TMP" catalogo.db config.tar.gz -C /opt/rayuela/demo fichas 2>/dev/null \
   | gpg --batch --yes --symmetric --cipher-algo AES256 --passphrase-file "$PASSFILE" \
         --output "$SALIDA" 2>>"$LOG"; then
  TAMANO=$(du -h "$SALIDA" | cut -f1)
  SHA=$(sha256sum "$SALIDA" | cut -d' ' -f1)
  echo "$(date '+%F %T') OK $SALIDA ($TAMANO) sha256=$SHA" >> "$LOG"
  echo "OK $SALIDA ($TAMANO) sha256=$SHA"
else
  echo "$(date '+%F %T') FALLA: no pude generar el paquete" >> "$LOG"
  rm -rf "$TMP"
  exit 1
fi

rm -rf "$TMP"

# 4) retencion: ultimos 5 paquetes
ls -1t "$DEST"/rayuela-*.tar.gz.gpg 2>/dev/null | tail -n +6 | while read -r viejo; do
  rm -f "$viejo"
  echo "$(date '+%F %T') borrado por antiguedad: $(basename "$viejo")" >> "$LOG"
done
