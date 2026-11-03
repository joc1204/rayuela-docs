#!/bin/bash
# Copia la base de produccion al ambiente de prueba.
# Uso: /root/refrescar-prueba.sh
set -e
echo "frenando el ambiente de prueba..."
systemctl stop ferias-prueba
sleep 1
sqlite3 /opt/rayuela/ferias/ferias.db ".backup '/opt/rayuela/prueba/ferias.db'"
chown rayuela:rayuela /opt/rayuela/prueba/ferias.db
echo "arrancando..."
systemctl start ferias-prueba
sleep 3
systemctl is-active ferias-prueba
curl -s -o /dev/null -w "  prueba /salud -> HTTP %{http_code}\n" --max-time 8 http://127.0.0.1:5051/salud
echo "listo: la prueba tiene los datos de produccion"
