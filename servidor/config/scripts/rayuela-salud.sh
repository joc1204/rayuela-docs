#!/bin/bash
# Salud de Rayuela: revisa servicios, HTTPS, disco, respaldos y certificados.
# Avisa por mail SOLO si hay problemas (y avisa cuando se recupera).
set -u

DIR_ESTADO=/var/lib/rayuela-salud
mkdir -p "$DIR_ESTADO"
ARCH_ESTADO="$DIR_ESTADO/estado"
ARCH_ULTIMO="$DIR_ESTADO/ultimo_aviso"
ENV_MAIL=/etc/rayuela/alerta.env

PROBLEMAS=()

# ---------- 1. servicios ----------
for s in ferias nginx fail2ban; do
    systemctl is-active --quiet "$s" || PROBLEMAS+=("Servicio $s no esta activo")
done
systemctl is-active --quiet ferias-prueba || PROBLEMAS+=("Servicio ferias-prueba no esta activo")

# ---------- 2. HTTPS publico ----------
for url in https://ferias.rayuelalaplata.com.ar/salud \
           https://lector.rayuelalaplata.com.ar/salud \
           https://prueba.rayuelalaplata.com.ar/salud; do
    cuerpo=$(curl -s --max-time 15 "$url" 2>/dev/null)
    echo "$cuerpo" | grep -q '"ok":true' || PROBLEMAS+=("No responde bien: $url")
done

# ---------- 3. novedades (netbook, por el tunel) ----------
cuerpo=$(curl -s --max-time 20 https://net-casa.tailfb7a36.ts.net/novedades/salud 2>/dev/null)
if echo "$cuerpo" | grep -q '"ok":true'; then
    :
else
    if echo "$cuerpo" | grep -q 'app'; then
        :   # responde, aunque sin ok:true (por ejemplo mail no configurado)
    else
        PROBLEMAS+=("Novedades no responde por el tunel")
    fi
fi

# ---------- 4. disco y memoria ----------
uso_disco=$(df -P / | awk 'NR==2 {gsub("%","",$5); print $5}')
[ "$uso_disco" -ge 85 ] && PROBLEMAS+=("Disco al ${uso_disco}%")
ram_libre=$(awk '/MemAvailable/ {print int($2/1024)}' /proc/meminfo)
[ "$ram_libre" -lt 100 ] && PROBLEMAS+=("Memoria disponible baja: ${ram_libre} MB")

# ---------- 5. respaldo de hoy ----------
hoy=$(date +%F)
respaldo="/var/backups/rayuela/ferias-$hoy.db.gz"
if [ ! -f "$respaldo" ]; then
    PROBLEMAS+=("Falta el respaldo de hoy ($respaldo)")
else
    edad_h=$(( ( $(date +%s) - $(stat -c %Y "$respaldo") ) / 3600 ))
    tam=$(stat -c %s "$respaldo")
    [ "$tam" -lt 2000 ] && PROBLEMAS+=("El respaldo de hoy es sospechosamente chico ($tam bytes)")
    [ "$edad_h" -gt 30 ] && PROBLEMAS+=("El respaldo de hoy tiene $edad_h horas")
fi

# ---------- 6. certificados ----------
while read -r nombre; do
    [ -z "$nombre" ] && continue
    fin=$(openssl x509 -in "/etc/letsencrypt/live/$nombre/cert.pem" -noout -enddate 2>/dev/null | cut -d= -f2)
    [ -z "$fin" ] && { PROBLEMAS+=("No pude leer el certificado $nombre"); continue; }
    dias=$(( ( $(date -d "$fin" +%s) - $(date +%s) ) / 86400 ))
    [ "$dias" -lt 14 ] && PROBLEMAS+=("El certificado $nombre vence en $dias dias")
done < <(ls -1 /etc/letsencrypt/live/ 2>/dev/null | grep -v README)

# ---------- resultado ----------
ahora=$(date +%s)

enviar_mail() {
    local asunto="$1" cuerpo="$2"
    [ -f "$ENV_MAIL" ] || { echo "falta $ENV_MAIL"; return 1; }
    python3 - "$asunto" "$cuerpo" <<'PY'
import os, sys, smtplib
from email.message import EmailMessage

def leer(ruta):
    datos = {}
    with open(ruta, encoding='utf-8') as f:
        for linea in f:
            linea = linea.strip()
            if linea and not linea.startswith('#') and '=' in linea:
                k, v = linea.split('=', 1)
                datos[k.strip()] = v.strip().strip('"')
    return datos

d = leer('/etc/rayuela/alerta.env')
msg = EmailMessage()
msg['From'] = d.get('ALERTA_REMITENTE', d['ALERTA_USUARIO'])
msg['To'] = d['ALERTA_DESTINO']
msg['Subject'] = sys.argv[1]
msg.set_content(sys.argv[2])
with smtplib.SMTP(d['ALERTA_HOST'], int(d['ALERTA_PUERTO']), timeout=30) as s:
    s.starttls()
    s.login(d['ALERTA_USUARIO'], d['ALERTA_CLAVE'])
    s.send_message(msg)
print('mail enviado')
PY
}

resumen_servidor=$(
    echo "Servidor: $(hostname) / $(date '+%F %T')"
    echo "Disco: ${uso_disco}% · RAM libre: ${ram_libre} MB"
    echo "Servicios: ferias=$(systemctl is-active ferias) nginx=$(systemctl is-active nginx) fail2ban=$(systemctl is-active fail2ban) prueba=$(systemctl is-active ferias-prueba)"
)

if [ ${#PROBLEMAS[@]} -eq 0 ]; then
    echo "OK: todo en orden"
    previo=$(cat "$ARCH_ESTADO" 2>/dev/null || echo "")
    if [ "$previo" = "con-problemas" ]; then
        enviar_mail "Rayuela: todo normalizado" \
"Se resolvieron los problemas detectados.

$resumen_servidor" || true
    fi
    echo "ok" > "$ARCH_ESTADO"
    exit 0
fi

texto=$(printf ' - %s\n' "${PROBLEMAS[@]}")
echo "PROBLEMAS:"
echo "$texto"

echo "con-problemas" > "$ARCH_ESTADO"
ultimo=$(cat "$ARCH_ULTIMO" 2>/dev/null || echo 0)
if [ $(( ahora - ultimo )) -ge 21600 ]; then   # no repetir antes de 6 horas
    enviar_mail "ALERTA Rayuela: ${#PROBLEMAS[@]} problema(s)" \
"Problemas detectados en Rayuela:

$texto
$resumen_servidor

Revisar: systemctl status ferias; journalctl -u ferias -n 50; df -h; ls -lh /var/backups/rayuela" && echo "$ahora" > "$ARCH_ULTIMO"
fi
exit 1
