#!/bin/bash
# Enriquecimiento en cadena: tanda tras tanda hasta que no queden libros por completar.
# No toca Rayuela: consulta librerias de terceros (sbs, yenny) a ritmo bajo.
#
# Independiente de la tienda: NO mira si el libro esta oculto o visible.
# Trabaja sobre publicables con stock positivo a los que les falta la sinopsis.
# Los que ya dieron "sin datos" en todas las fuentes quedan registrados y no se repiten.
#
# Se detiene solo (y se puede detener a mano):
#   - si no quedan libros con stock sin editorial o sin sinopsis
#   - si dos tandas seguidas no suman datos nuevos
#   - si existe el archivo /etc/rayuela/pausa-enriquecido
set -u

DB=/opt/rayuela/demo/catalogo.db
PY=/opt/rayuela/novedades/venv/bin/python
SCRIPT=/opt/rayuela/demo/enriquecer_externos.py
LOG=/var/log/rayuela-enriquecido.log
PAUSA=/etc/rayuela/pausa-enriquecido
LOTE=4000

restantes() {
  sqlite3 "$DB" "SELECT COUNT(*) FROM productos p
                   WHERE p.publicable = 1 AND p.oculto = 0 AND p.stock > 0
                     AND (p.detalle IS NULL OR p.detalle = '')
                     AND p.codigo NOT IN (
                       SELECT codigo FROM intentos_enriquecido
                       WHERE resultado = 'sin_datos'
                       GROUP BY codigo HAVING COUNT(DISTINCT fuente) >= 3);" 2>/dev/null || echo 0
}

echo "$(date '+%F %T') === arranca el enriquecimiento en cadena ===" >> "$LOG"
estancadas=0
tanda=0

while true; do
  if [ -f "$PAUSA" ]; then
    echo "$(date '+%F %T') detenido a mano ($PAUSA)" >> "$LOG"
    break
  fi

  antes=$(restantes)
  if [ "${antes:-0}" -le 0 ]; then
    echo "$(date '+%F %T') no quedan pendientes: terminado" >> "$LOG"
    break
  fi

  tanda=$((tanda + 1))
  echo "$(date '+%F %T') --- tanda $tanda · pendientes: $antes ---" >> "$LOG"
  sleep 20

  cd /opt/rayuela/novedades || exit 1
  "$PY" "$SCRIPT" --limite "$LOTE" --pausa 0.8 --sitios sbs,yenny,zivals --solo-sinopsis >> "$LOG" 2>&1

  despues=$(restantes)
  ganancia=$((antes - despues))
  echo "$(date '+%F %T') tanda $tanda: $antes -> $despues (mejoro $ganancia)" >> "$LOG"

  if [ "$ganancia" -le 0 ]; then
    estancadas=$((estancadas + 1))
    echo "$(date '+%F %T') sin avance ($estancadas de 2)" >> "$LOG"
    [ "$estancadas" -ge 2 ] && { echo "$(date '+%F %T') dos tandas sin avance: termino" >> "$LOG"; break; }
  else
    estancadas=0
  fi
done

echo "$(date '+%F %T') === fin del enriquecimiento en cadena ===" >> "$LOG"
