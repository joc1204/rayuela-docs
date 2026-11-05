#!/bin/bash
# Genera el respaldo cifrado y lo sube a Google Drive.
# Pensado para correr por timer (03:40). Si Drive no esta configurado, avisa y no rompe.
set -u
DEST=/var/backups/rayuela/externo
LOG=$DEST/respaldo-nube.log
REMOTO=drive:Rayuela-respaldo
RETENER=3

mkdir -p "$DEST"
echo "$(date '+%F %T') === respaldo a la nube ===" >> "$LOG"

# 1) paquete local (catalogo + fichas + config, cifrado)
if ! bash /usr/local/bin/respaldo-externo.sh >> "$LOG" 2>&1; then
  echo "$(date '+%F %T') FALLA generando el paquete" >> "$LOG"
  exit 1
fi
ARCHIVO=$(ls -t "$DEST"/rayuela-*.tar.gz.gpg 2>/dev/null | head -1)
if [ -z "$ARCHIVO" ]; then
  echo "$(date '+%F %T') FALLA: no hay paquete para subir" >> "$LOG"
  exit 1
fi

# 2) configuracion de rclone
if ! rclone listremotes 2>/dev/null | grep -q '^drive:'; then
  echo "$(date '+%F %T') AVISO: Drive no configurado (falta el token). No se sube nada." >> "$LOG"
  exit 0
fi

# 3) subida
if rclone copy "$ARCHIVO" "$REMOTO" --no-traverse --stats-one-line >> "$LOG" 2>&1; then
  echo "$(date '+%F %T') OK subido: $(basename "$ARCHIVO") ($(du -h "$ARCHIVO" | cut -f1))" >> "$LOG"
else
  echo "$(date '+%F %T') FALLA: no se pudo subir a Drive" >> "$LOG"
  exit 1
fi

# 4) retencion en Drive: quedan los ultimos N paquetes
rclone lsf "$REMOTO" --files-only 2>/dev/null | grep -E '^rayuela-.*\.tar\.gz\.gpg$' \
  | sort -r | tail -n +$((RETENER + 1)) | while read -r viejo; do
  rclone deletefile "$REMOTO/$viejo" 2>/dev/null
  echo "$(date '+%F %T') borrado en Drive por antiguedad: $viejo" >> "$LOG"
done

echo "$(date '+%F %T') fin" >> "$LOG"
