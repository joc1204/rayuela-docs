#!/bin/bash
# Respaldo diario: base de ferias + configuraciones del servidor.
# Base: /var/backups/rayuela  |  Retencion: 14 dias
set -u
DEST=/var/backups/rayuela
FECHA=$(date +%Y-%m-%d)
mkdir -p "$DEST"
LOG="$DEST/respaldo.log"

# 1. base (con sqlite3 .backup: consistente aunque la app este escribiendo)
TMP=$(mktemp /tmp/ferias-XXXXXX.db)
if sqlite3 /opt/rayuela/ferias/ferias.db ".backup '$TMP'"; then
  LIBROS=$(sqlite3 "$TMP" "select count(*) from libros;" 2>/dev/null || echo ERR)
  if [ "$LIBROS" = "ERR" ] || [ -z "$LIBROS" ]; then
    echo "$(date '+%F %T') FALLA: el dump no abre" >> "$LOG"
    rm -f "$TMP"
    exit 1
  fi
  gzip -9 -c "$TMP" > "$DEST/ferias-$FECHA.db.gz"
  rm -f "$TMP"
  echo "$(date '+%F %T') OK base: $LIBROS libros -> ferias-$FECHA.db.gz ($(du -h "$DEST/ferias-$FECHA.db.gz" | cut -f1))" >> "$LOG"
else
  echo "$(date '+%F %T') FALLA: sqlite3 no pudo copiar" >> "$LOG"
  exit 1
fi

# 2. configuraciones (nginx, systemd, ssh, letsencrypt) una vez por dia
TAR="$DEST/config-$FECHA.tar.gz"
tar czf "$TAR" -C / \
    etc/nginx/sites-available etc/nginx/conf.d etc/nginx/nginx.conf \
    etc/systemd/system/ferias.service etc/systemd/system/ferias-prueba.service \
    etc/ssh/sshd_config etc/ssh/sshd_config.d \
    etc/letsencrypt/renewal 2>/dev/null
echo "$(date '+%F %T') OK config -> config-$FECHA.tar.gz" >> "$LOG"


# 1b. catalogo de la demo (55 MB, se comprime bien)
if [ -f /opt/rayuela/demo/catalogo.db ]; then
  TMPC=$(mktemp /tmp/catalogo-XXXXXX.db)
  if sqlite3 /opt/rayuela/demo/catalogo.db ".backup '$TMPC'"; then
    gzip -6 -c "$TMPC" > "$DEST/catalogo-$FECHA.db.gz"
    echo "$(date '+%F %T') OK catalogo -> catalogo-$FECHA.db.gz ($(du -h "$DEST/catalogo-$FECHA.db.gz" | cut -f1))" >> "$LOG"
  else
    echo "$(date '+%F %T') FALLA: no pude copiar el catalogo" >> "$LOG"
  fi
  rm -f "$TMPC"
fi

# 3. limpieza: 14 dias
find "$DEST" -name 'ferias-*.db.gz' -mtime +14 -delete
find "$DEST" -name 'config-*.tar.gz' -mtime +14 -delete
find "$DEST" -name 'catalogo-*.db.gz' -mtime +14 -delete

# 4. resumen al log del sistema (queda en journalctl)
echo "respaldo rayuela: $(ls -1 "$DEST"/ferias-*.db.gz 2>/dev/null | wc -l) bases y $(ls -1 "$DEST"/config-*.tar.gz 2>/dev/null | wc -l) configs guardadas"
