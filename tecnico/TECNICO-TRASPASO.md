# Rayuela · Documento técnico y de traspaso

> **Qué es este documento.** Todo lo necesario para operar, mantener y —si hace
> falta— entregar la infraestructura digital de la librería Rayuela a otra persona.
> No es el manual del usuario final: para eso están `manual/Manual-Rayuela-Ferias`
> y `manual_novedades/Guia-Novedades`.
>
> **Última actualización:** 03/11/2026
> **Estado:** refleja lo verificado en el servidor en esa fecha, no lo que se supone.

---

## Índice

1. [Resumen y mapa](#1-resumen-y-mapa)
2. [Proveedores y cuentas](#2-proveedores-y-cuentas)
3. [Infraestructura](#3-infraestructura)
4. [Aplicaciones](#4-aplicaciones)
5. [Base de datos](#5-base-de-datos)
6. [Procedimientos (runbook)](#6-procedimientos-runbook)
7. [Seguridad](#7-seguridad)
8. [Respaldos y recuperación](#8-respaldos-y-recuperación)
9. [Pruebas](#9-pruebas)
10. [Estado del proyecto](#10-estado-del-proyecto)
11. [Riesgos y deuda técnica](#11-riesgos-y-deuda-técnica)
12. [Checklist de traspaso](#12-checklist-de-traspaso)
13. [Glosario](#13-glosario)

---

## 1. Resumen y mapa

Rayuela tiene dos grupos de sistemas:

- **Digitales propios** (los que mantiene Jorge): app de ferias + lectores de precios,
  bot de novedades, ambiente de prueba.
- **Digitales heredados** (de la librería, con otro responsable histórico): sitio web
  actual y correo del dominio, ambos en Hostinger; sistema de gestión **Bridge**,
  que es el dueño de los datos comerciales (precios, stock, ventas del local).

```
                    ┌──────────────────────────────────────────┐
   NIC.ar  (titular:│  rayuelalibros.com.ar  → nameservers      │
   Rayuela)         │  hyperion/atlas.dns-parking.com (Hostinger)│
                    │    · web actual (Hostinger)               │
                    │    · correo (MX Hostinger, ~25 años)      │
                    └──────────────────────────────────────────┘

   NIC.ar (titular: Rayuela)
   rayuelalaplata.com.ar  →  NS Cloudflare (nina / cosmin)
        │
        ├── ferias.rayuelalaplata.com.ar   → VPS   (app + panel admin)
        ├── lector.rayuelalaplata.com.ar   → VPS   (lector público + vendedor)
        ├── prueba.rayuelalaplata.com.ar   → VPS   (ambiente de prueba)
        └── (apex sin registro: no existe web pública)

   VPS DonWeb 201.32.132.197 (Ubuntu 24.04)
        ├── nginx  → HTTPS, límites, cabeceras
        ├── ferias.service       :5050  producción
        ├── ferias-prueba.service:5051  prueba
        ├── fail2ban, ufw, certbot (3 certificados)
        └── SQLite: /opt/rayuela/ferias/ferias.db

   Netbook del local 192.168.1.19 (Debian 32 bits)
        ├── rayuela-novedades.service :5060   (bot de novedades)
        ├── gastos.service            :5000   (Cuenta Clara, de Jorge)
        ├── presupuestito.service     :5001   (Presupuestito, de Jorge)
        ├── Node-RED                   :1880  (automatizaciones)
        └── Tailscale Funnel: net-casa.tailfb7a36.ts.net
```

**Datos comerciales**: los precios que muestra el lector se consultan en vivo a **Bridge**,
por un endpoint **NO documentado** (`/BSGestion/BuscadorProductosAction.do`, solo lectura,
por ISBN, sin stock), descubierto a partir de los puestos de autoconsulta del salón.
No tiene soporte oficial: puede cambiar sin aviso. La API documentada de Bridge (versión
vieja y nueva) es el camino correcto para el futuro; ver §11.
La app de ferias guarda sus propios datos (stock de feria, ventas de feria) en SQLite.

---

## 2. Proveedores y cuentas

| Proveedor | Qué se contrata | Dónde se administra | Titular | Quién tiene acceso | Costo |
|---|---|---|---|---|---|
| **NIC.ar** | Registro de dominios `.com.ar` / `.ar` | https://nic.ar (CUIT/CUIL + Clave Fiscal nivel 2+ vía TAD) | **Rayuela** | Verónica / contador; Fermín hizo la última delegación | Anual, bajo |
| **Cloudflare** | DNS de `rayuelalaplata.com.ar` (plan Free) | https://dash.cloudflare.com | **Cuenta personal de Jorge** | Jorge | Gratis |
| **DonWeb** | VPS Cloud Server plan 2 (2 vCPU, 2 GB RAM, 10 GB SSD, 1 TB/mes, DC Argentina) | Panel de DonWeb | Rayuela / Jorge | Jorge | ~ARS 15.000–16.700/mes |
| **Hostinger** | Correo del dominio `rayuelalibros.com.ar` y sitio web actual | Panel de Hostinger (`dns-parking`) | **Rayuela** (cuenta con ~25 años) | Rayuela (el ex-programador tuvo acceso) | Según plan contratado |
| **Resend** | Envío de correo de la app (dominio 
ayuelalaplata.com.ar autenticado, plan Free 3.000/mes) | https://resend.com | Cuenta personal de Jorge | Jorge | Gratis |
| **Tailscale** | Túnel del netbook (`net-casa.tailfb7a36.ts.net`) | https://login.tailscale.com | Jorge | Jorge | Gratis |
| **Gmail** | Correo actual del bot de novedades (a reemplazar por Brevo) | `jorge.domotica34@gmail.com` | Jorge | Jorge | Gratis |

### Credenciales: dónde viven (nunca en este documento)

| Credencial | Ubicación |
|---|---|
| Clave SSH del VPS | `C:\Users\Jorge\Documents\deepseek-harness\default-workspace\.ssh_keys\ferias_ed25519` (privada) |
| Clave SSH del netbook | `.ssh_keys\id_rsa` |
| Contraseña de root del VPS | Solo para la **consola VNC** del panel de DonWeb (el SSH no acepta contraseña) |
| `FERIAS_SECRETO` (firma de sesiones) | En el archivo de unidad `/etc/systemd/system/ferias.service` |
| Clave SMTP de Novedades | `/home/jorge/rayuela_scrapping/servicio/.env` en el netbook |
| PIN de la app de Novedades | Idem (`NOVEDADES_PIN`) |
| Claves de usuario de la app de ferias | Solo hashes (scrypt) en la base |

> **Al traspasar**: entregar las claves por un canal seguro (gestor de contraseñas, no
> por mail), y **rotarlas todas** después del traspaso.

---

## 3. Infraestructura

### 3.1 VPS

| Dato | Valor |
|---|---|
| IP pública | `201.32.132.197` |
| Hostname | `vps-6586187-x` |
| Sistema | Ubuntu 24.04.5 LTS, kernel 6.8.0-147 |
| CPU / RAM / Disco | 2 vCPU / 1960 MB / 14 GB (12 GB libres al 03/11) |
| Zona horaria | America/Argentina/Buenos_Aires |
| SSH | puerto **5186**, solo con clave (`PasswordAuthentication no`, `PermitRootLogin prohibit-password`). El puerto 22 se cerró el 03/11/2026 |
| Puertos abiertos (ufw) | 5186/tcp, 80/tcp, 443/tcp |
| Acceso de emergencia | **Consola VNC** del panel de DonWeb (contraseña de root) |

**Servicios activos**: `ferias` (5050), `ferias-prueba` (5051), `nginx`, `fail2ban`,
`unattended-upgrades`, `rayuela-respaldo.timer` (respaldo diario 03:10, ver §8) y
`rayuela-salud.timer` (monitoreo cada 30 minutos, ver §6.10). Los dos servicios de la app escuchan **solo en 127.0.0.1**: no
son accesibles desde internet sin pasar por nginx.

### 3.2 nginx

Sitios en `/etc/nginx/sites-available/` (enlazados en `sites-enabled/`):

| Archivo | Sirve |
|---|---|
| `frerias` → ver `ferias` | `201.32.132.197.sslip.io` y la IP — **nombre temporal de respaldo** (se retira cuando se confirme el uso en celulares) |
| `rayuela-apps` | `ferias.rayuelalaplata.com.ar` (app) y `lector.rayuelalaplata.com.ar` (lector directo en `/`) |
| `prueba` | `prueba.rayuelalaplata.com.ar` (ambiente de prueba + cartel inyectado con `sub_filter`) |

Archivos compartidos:

| Archivo | Contenido |
|---|---|
| `/etc/nginx/conf.d/99-rayuela.conf` | `server_tokens off`, `limit_req_status 429`, zonas de límite (`rayuela_general` 20 r/s, `rayuela_login` 30 r/m, `rayuela_conn`), y `map $request_uri $rayuela_basura` que corta rutas de escaneo (`.env`, `.git`, `wp-*`, `phpmyadmin`, `*.php`, etc.) con `444` |
| `/etc/nginx/proxy_rayuela.conf` | Cabeceras de proxy (`Host`, `X-Real-IP`, `X-Forwarded-*`) |

Cabeceras de seguridad en los bloques HTTPS: `Strict-Transport-Security`,
`X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`, `Referrer-Policy`,
`Permissions-Policy` (cámara solo mismo origen), `X-Robots-Tag: noindex`,
`Content-Security-Policy`.

Límites por bloque: `limit_conn rayuela_conn 20`, `limit_req zone=rayuela_general
burst=40 nodelay`, y en `location = /ingresar` `limit_req zone=rayuela_login burst=10`.
Timeouts de cuerpo/cabecera 15 s (frena slowloris).

### 3.3 Certificados (Let's Encrypt, renovación automática con `certbot.timer`)

| Nombre | Dominios | Vence |
|---|---|---|
| `rayuela-apps` | `ferias.` y `lector.rayuelalaplata.com.ar` | 31/01/2027 |
| `prueba.rayuelalaplata.com.ar` | `prueba.…` | 01/02/2027 |
| `201.32.132.197.sslip.io` | el nombre temporal | 30/01/2027 |

La validación es **HTTP-01 por webroot** (`/var/www/html`), por eso los bloques del
puerto 80 tienen `location /.well-known/acme-challenge/` **antes** del redirect.

> **Error histórico a no repetir**: un `return 301` a nivel de `server` se ejecuta
> antes de elegir el `location`, y rompe el challenge. El `return` tiene que estar
> dentro de `location /`.

### 3.4 DNS

**`rayuelalaplata.com.ar`** (gestionado en Cloudflare, **sin proxy: nube gris**):

| Registro | Nombre | Valor |
|---|---|---|
| A | `ferias` | 201.32.132.197 |
| A | `lector` | 201.32.132.197 |
| A | `prueba` | 201.32.132.197 |
| — | apex (`@`) | **sin registro**: no existe web pública (decisión: el apex queda para el portal futuro) |

Nameservers: `nina.ns.cloudflare.com`, `cosmin.ns.cloudflare.com` (delegados desde NIC.ar).

**`rayuelalibros.com.ar`** (Hostinger, **no tocar sin plan**: tiene el correo de Rayuela):

| Registro | Valor | Nota |
|---|---|---|
| A `@` | 147.79.105.238 · 89.116.213.115 | sitio actual |
| AAAA `@` | 2a02:4780:18:31b:b889:22cd:de88:caf0 · 2a02:4780:2f:64b:f650:d824:c048:5767 | idem |
| CNAME `www` | `www.rayuelalibros.com.ar.cdn.hstgr.net` | |
| MX | `mx1.hostinger.com` (5) · `mx2.hostinger.com` (10) | **correo** |
| TXT `@` | `v=spf1 include:_spf.mail.hostinger.com ~all` | SPF |
| CNAME `autodiscover` | `autodiscover.mail.hostinger.com` | clientes de correo |
| TXT `_dmarc` | `v=DMARC1; p=none` | |
| TXT `hostingermail-a._domainkey` | DKIM completo | firma del correo |
| NS | `hyperion.dns-parking.com`, `atlas.dns-parking.com` | Hostinger |

> Si algún día hay que mudar ese DNS, **copiar los 10 registros** (incluido DKIM) y
> probar el correo antes y después. Windows/Outlook usan `autodiscover`.

### 3.5 Netbook del local

| Dato | Valor |
|---|---|
| IP / usuario | `192.168.1.19` / `jorge` (**sin sudo**: usar `su -` y la clave de root) |
| Sistema | Debian de 32 bits (hardware viejo, funciona como servidor local) |
| Túnel | `net-casa.tailfb7a36.ts.net`, configuración en `/etc/tunel-apps.conf`, verificador `funnel-check` |
| Servicios | `rayuela-novedades` (5060), `gastos` (5000), `presupuestito` (5001), Node-RED (1880) |
| **App de ferias** | **detenida y deshabilitada** (migró al VPS el 01/11/2026) |

El túnel publica `/gastos`, `/presupuestos`, `/novedades` y otros. Republicar el túnel
corta el servicio 30-40 segundos.

---

## 4. Aplicaciones

### 4.1 App de ferias + lector de precios (Flask)

| Dato | Valor |
|---|---|
| Código | `/opt/rayuela/ferias` (dueño `rayuela`) |
| Servicio | `ferias.service`, puerto 5050, `Restart=always` |
| Base | `/opt/rayuela/ferias/ferias.db` (SQLite) |
| Entorno virtual | `/opt/rayuela/ferias/venv` (Python 3.12.3, Flask 3.1.3) |
| Variables | `FERIAS_PUERTO=5050`, `FERIAS_DB=…`, `FERIAS_PREFIJO=` (vacío), `FERIAS_SECURE=1`, `FERIAS_SECRETO=<64 hex>` |
| Endurecimiento de la unidad | `NoNewPrivileges`, `PrivateTmp`, `ProtectSystem=full`, `ReadWritePaths=/opt/rayuela/ferias` |

**Funciones**: ferias, stock por feria, ventas, caja, reposiciones, reservas, precios,
usuarios con roles, manual (`/manual`), estado (`/salud`), `robots.txt` con `Disallow: /`.

**Lector de precios** (misma app):

| URL | Modo |
|---|---|
| `https://lector.rayuelalaplata.com.ar` | **cliente**: escanea, arma lista de deseos, copia o envía por WhatsApp |
| `https://lector.rayuelalaplata.com.ar/?m=v` (también `?modo=vendedor`) | **vendedor**: ficha completa + casilla "Armar lista" |

Detalles del lector: corte por inactividad de 30 minutos (fijo hoy, se hará
configurable), cámara liberada al cambiar de pestaña (`visibilitychange`), lista en
memoria (hoy se pierde al recargar: se va a persistir), mensaje formateado por
`static/lector_lista.js` (probado aparte con Node).

**Seguridad de la app**: 10 intentos fallidos por IP en 15 min → bloqueo 15 min (HTTP
429); claves de 8 caracteres mínimo; sesiones con cookie firmada (`FERIAS_SECRETO`).

### 4.2 Ambiente de prueba

| Dato | Valor |
|---|---|
| Código | `/opt/rayuela/prueba` (copia de producción) |
| Servicio | `ferias-prueba.service`, puerto 5051, **secreto propio** |
| Base | `/opt/rayuela/prueba/ferias.db` (copia) |
| URL | `https://prueba.rayuelalaplata.com.ar` |
| Cartel | Inyectado por nginx con `sub_filter` al final del `</body>`: "AMBIENTE DE PRUEBA - los datos no son reales" |
| Refrescar datos | `sudo /root/refrescar-prueba.sh` (frena, copia con `sqlite3 .backup`, arranca) |

Regla de trabajo: **nada se instala en producción sin pasar por `prueba.`**.

### 4.3 Bot de novedades (scraping)

| Dato | Valor |
|---|---|
| Código | `/home/jorge/rayuela_scrapping` en el netbook |
| Servicio | `rayuela-novedades.service`, puerto 5060 |
| URL | `https://net-casa.tailfb7a36.ts.net/novedades` |
| Config | `/home/jorge/rayuela_scrapping/servicio/.env` (SMTP, PIN) |
| PIN actual | en ese `.env` (no en este documento) |
| Uso | escanea sitios de editoriales/distribuidoras, encuentra novedades, arma planillas y las manda por mail |

### 4.4 Otros (de Jorge, no de Rayuela)

`gastos` (Cuenta Clara, 5000), `presupuestito` (5001), Node-RED (1880). Proyectos
separados: no se mezclan con los de Rayuela.

---

## 5. Base de datos

SQLite, un archivo: `/opt/rayuela/ferias/ferias.db` (180 KB al 03/11/2026).

| Tabla | Contenido |
|---|---|
| `ferias` | eventos (nombre, lugar, fecha, estado) |
| `libros` | catálogo propio: ISBN, título, autor, precio, editorial, colección, temas |
| `feria_libros` | stock por feria (un libro por feria con cantidad) |
| `movimientos` | historial de stock/cambios por feria |
| `ventas`, `venta_items` | ventas de feria |
| `formas_pago` | medios de pago |
| `arqueos` | cierres de caja |
| `reservas`, `reserva_items` | reservas |
| `reposiciones` | reposiciones |
| `clientes` | clientes (futuro: listas de deseos) |
| `usuarios` | usuarios con rol (`admin`, `vendedor`, `repositor`) y hash scrypt |
| `dispositivos` | dispositivos/lectores registrados |
| `contadores` | numeración interna |
| `ajustes` | configuración de la app |

### Comandos

```bash
# respaldo consistente (no copiar el archivo a mano con la app escribiendo)
sudo -u rayuela sqlite3 /opt/rayuela/ferias/ferias.db ".backup '/root/ferias-$(date +%F).db'"

# inspeccionar
sudo -u rayuela sqlite3 /opt/rayuela/ferias/ferias.db "select count(*) from libros;"

# restaurar (con el servicio detenido)
sudo systemctl stop ferias
sudo cp /root/ferias-2026-11-03.db /opt/rayuela/ferias/ferias.db
sudo chown rayuela:rayuela /opt/rayuela/ferias/ferias.db
sudo systemctl start ferias
```

---

## 6. Procedimientos (runbook)

### 6.1 Verificación rápida (siempre lo primero)

```bash
# en el VPS
systemctl is-active ferias ferias-prueba nginx fail2ban
curl -s https://ferias.rayuelalaplata.com.ar/salud      # {"app":"ferias","ok":true}
curl -s https://lector.rayuelalaplata.com.ar/salud      # 200
df -h / | tail -1
```

```powershell
# desde cualquier máquina (externo, es lo que vale)
# abrir https://ferias.rayuelalaplata.com.ar/salud en el navegador
```

### 6.2 Acceso al VPS

```powershell
ssh -i .ssh_keys\ferias_ed25519 -p 5186 root@201.32.132.197
```

Si el SSH no responde: panel de DonWeb → **Consola VNC** → entrar como root con la
contraseña del servidor (el SSH no acepta contraseña a propósito).

### 6.3 Deploy de la app de ferias

```bash
# 1. en la PC: pruebas locales
python tests_flujo.py          # tiene que decir TODO OK

# 2. copiar solo lo que cambió (nunca el venv ni ferias.db)
scp -i .ssh_keys/ferias_ed25519 -P 5186 <archivos> root@201.32.132.197:/opt/rayuela/ferias/

# 3. dueño + reinicio
ssh ... 'chown -R rayuela:rayuela /opt/rayuela/ferias && systemctl restart ferias'

# 4. verificar desde afuera, no desde el servidor
```

- Cambios en **estáticos** (`.js`, `.css`, imágenes): no requieren reinicio.
- Cambios en **plantillas** (`.html`): requieren reinicio.
- Si se toca el lector: **subir el `?v=`** en `base.html` / `lector.html` (los celulares cachean).

### 6.4 Deploy en el ambiente de prueba (recomendado antes de producción)

```bash
rsync -a --exclude venv --exclude 'ferias.db*' --exclude __pycache__ \
      /opt/rayuela/ferias/ /opt/rayuela/prueba/
chown -R rayuela:rayuela /opt/rayuela/prueba
systemctl restart ferias-prueba
```

### 6.5 Agregar un subdominio nuevo

1. Cloudflare → DNS → `A <nombre> 201.32.132.197`, **DNS only**
2. En el VPS: copiar un bloque de `sites-available/rayuela-apps` y cambiar `server_name`
3. Primero solo puerto 80 (con el `location /.well-known/acme-challenge/`), `nginx -t`,
   `reload`
4. `certbot certonly --webroot -w /var/www/html -d <nombre> --non-interactive --agree-tos -m <mail>`
5. Agregar el bloque 443 con el certificado nuevo, `nginx -t`, `reload`
6. Verificar **desde afuera**

### 6.6 Renovación de certificados

Automática (`certbot.timer`, dos veces por día). Verificar:

```bash
certbot certificates
certbot renew --dry-run     # prueba sin emitir
```

### 6.7 Rollback

| Caso | Cómo |
|---|---|
| Código mal instalado | Restaurar los archivos anteriores (copia previa o `git` del workspace) + `systemctl restart ferias` |
| Base dañada | Restaurar el último respaldo (5. Comandos) |
| Volver a la netbook (ferias) | En el netbook: `su -`, `systemctl enable --now ferias` (tiene la misma base y claves) |
| Dominio con problemas | El nombre temporal `https://201.32.132.197.sslip.io` sigue activo como respaldo |

### 6.8 Rotar una credencial

| Credencial | Cómo |
|---|---|
| `FERIAS_SECRETO` | Editar `Environment=` en `/etc/systemd/system/ferias.service`, `daemon-reload`, `restart` (invalida todas las sesiones) |
| Clave de usuario de la app | Panel → Usuarios → cambiar clave |
| Clave SMTP | Panel de Brevo → revocar y generar nueva → actualizar `.env` → `restart` |
| Clave SSH | Generar par nuevo, agregar la pública a `/root/.ssh/authorized_keys`, probar, **después** borrar la vieja |

### 6.9 Respaldos (automático, diario 03:10)

El timer `rayuela-respaldo.timer` ejecuta `/usr/local/bin/rayuela-respaldo.sh`, que:

1. Hace un dump **consistente** de la base (`sqlite3 .backup`) y lo comprime en
   `/var/backups/rayuela/ferias-AAAA-MM-DD.db.gz`
2. **Verifica** que el dump abra y tenga libros (si falla, deja "FALLA" en el log y sale con error)
3. Guarda un tar con las configuraciones (`nginx`, unidades de systemd, `sshd_config`,
   renovación de Let's Encrypt) en `config-AAAA-MM-DD.tar.gz`
4. Borra lo que tenga más de 14 días

```bash
# ver estado
systemctl list-timers rayuela-respaldo.timer
cat /var/backups/rayuela/respaldo.log | tail -5

# forzar un respaldo ahora
systemctl start rayuela-respaldo.service

# restaurar la base desde un respaldo
systemctl stop ferias
zcat /var/backups/rayuela/ferias-2026-11-03.db.gz > /opt/rayuela/ferias/ferias.db
chown rayuela:rayuela /opt/rayuela/ferias/ferias.db
systemctl start ferias
curl -s https://ferias.rayuelalaplata.com.ar/salud
```

> Los respaldos están **en el mismo servidor**: sirven para errores de datos y
> restauraciones puntuales, no para perder el servidor entero (para eso está el
> snapshot de DonWeb). Si en el futuro se quiere copia fuera del servidor, se puede
> bajar el `.db.gz` por `scp` o sincronizar a otro lado.

---

### 6.10 Monitoreo automático (`rayuela-salud`)

Cada 30 minutos, `/usr/local/bin/rayuela-salud.sh` verifica:

| Qué | Falla si… |
|---|---|
| Servicios | `ferias`, `ferias-prueba`, `nginx` o `fail2ban` no están activos |
| HTTPS público | `ferias.`, `lector.` o `prueba.` no responden `{"ok":true}` |
| Novedades | no responde por el túnel |
| Disco / memoria | disco ≥ 85 % o menos de 100 MB de RAM libre |
| Respaldo del día | falta, pesa menos de 2 KB o tiene más de 30 h |
| Certificados | a alguno le quedan menos de 14 días |

**Avisa solo cuando hay problemas** (máximo un aviso cada 6 h para no spamear) y
manda un mail de "todo normalizado" cuando se resuelve. Credenciales en
`/etc/rayuela/alerta.env` (permisos 600, solo root).

```bash
# correrlo a mano
/usr/local/bin/rayuela-salud.sh

# ver cuándo corrió y qué dijo
systemctl list-timers rayuela-salud.timer
journalctl -u rayuela-salud.service -n 30 --no-pager
```

---
## 7. Seguridad

### 7.1 Qué está aplicado

**SSH**: puerto 5186, solo clave pública, `PermitRootLogin prohibit-password`,
`PasswordAuthentication no`.

> **Atención al cambiar el puerto de SSH**: Ubuntu 24.04 usa activación por socket.
> Los puertos que escucha se generan desde `Port` de `sshd_config` con
> `sshd-socket-generator`. Después de cambiar `Port` hay que hacer
> `systemctl daemon-reload` y **reiniciar `ssh.socket`** (no alcanza con recargar
> `ssh.service`): un `reload` deja los sockets viejos abiertos.

**Firewall (ufw)**: solo 5186, 80 y 443.

**fail2ban** (dos cárceles):

| Cárcel | Regla | Ban |
|---|---|---|
| `sshd` | 4 fallas | 24 h |
| `nginx-rayuela-limit` | 5 excesos del límite de nginx | 6 h |

`ignoreip` incluye 127.0.0.1 y la IP del propio VPS (para no autobloquearse al probar).

**nginx**: `server_tokens off` (no revela versión), rutas de escaneo cortadas con 444,
límites de tasa y de conexiones, timeouts cortos, cabeceras de seguridad, HSTS.

**Aplicación**: freno de intentos en el login (10 fallas por IP en 15 min → 429 y
bloqueo 15 min), claves de 8 caracteres mínimo, `robots.txt` con `Disallow: /`,
cabecera `X-Robots-Tag: noindex` (el sitio no se indexa).

**Sistema**: actualizaciones de seguridad automáticas (`unattended-upgrades`), servicios
con usuario no privilegiado `rayuela` y `ProtectSystem=full`.

### 7.2 Qué hacer si hay un incidente

1. **Sospecha de acceso**: `last -20`, `journalctl -u sshd --since today`,
   `fail2ban-client status sshd`
2. **Bloquear**: `fail2ban-client set sshd banip <ip>` (o regla ufw)
3. **Sospecha de compromiso**: cambiar contraseña de root (consola), rotar
   `FERIAS_SECRETO`, rotar claves de usuario, revisar `/root/.ssh/authorized_keys`
4. **Restaurar** desde respaldo si hay datos alterados
5. **Registrar** qué pasó, cuándo y qué se cambió

### 7.3 Pendiente (ver §11)

Respaldo automático de la base, cierre definitivo del puerto 22 en sshd, y sacar el
nombre temporal `sslip.io` cuando ya no haga falta.

---

## 8. Respaldos y recuperación

### 8.1 Qué hay hoy

| Respaldo | Frecuencia | Dónde |
|---|---|---|
| Snapshot del VPS | Diario (plan Premium de DonWeb) | Panel de DonWeb |
| **Dump automático de la base + configuraciones** | **Diario 03:10** (retención 14 días) | `/var/backups/rayuela/` — ver §6.9 |
| Copia manual de la base | Puntual, antes de cambios de datos | `/opt/rayuela/ferias/ferias.db.antes-de-…` y `/root/` |
| Base de la netbook (ex ferias) | Congelada al 01/11/2026 | netbook `/home/jorge/ferias/ferias.db` |
| Repositorios de código | Git privado | GitHub `rayuela-ferias`, `rayuela-novedades` |

**RPO actual**: **24 h** (dump propio diario + snapshot diario del proveedor). **RTO
estimado**: 10-15 minutos (restaurar archivo de base y reiniciar el servicio).

### 8.2 Cómo restaurar el servidor completo

1. Panel de DonWeb → restaurar el snapshot elegido
2. Verificar: `systemctl status ferias nginx`, `curl https://ferias.…/salud`
3. Si el snapshot es viejo, restaurar la base del último dump disponible

---

## 9. Pruebas

| Qué | Comando | Resultado esperado |
|---|---|---|
| App de ferias (215 verificaciones) | `cd ferias_app && python tests_flujo.py` | `TODO OK`, 0 fallas |
| Formato del mensaje de la lista (12) | `node ferias_app/_test_texto_lista.js` | `TODO OK` |
| Scraper de novedades | `python tests/test_sitios.py` (+ `test_isbn`, `test_web`) | `TODO OK` |

Las pruebas de ferias usan una base temporal (`FERIAS_DB=_test_tmp`) y **no tocan
producción**. En el servidor corren con:
`runuser -u rayuela -- ./venv/bin/python tests_flujo.py`

---

## 10. Estado del proyecto

### Hecho y en producción

- App de ferias migrada del netbook al VPS (HTTPS, dominio propio, 215 pruebas OK)
- Lector de precios con dos modos (cliente / vendedor) y mensaje de WhatsApp
- Endurecimiento completo (SSH, firewall, fail2ban, nginx, app)
- Ambiente de prueba independiente con cartel identificatorio
- Repositorios privados de código
- QR definitivos generados y verificados
- Netbook con la app de ferias **detenida y deshabilitada** (rollback disponible)

### En curso / próximos

Ver **`RAYUELA-BACKLOG.md`** (módulos aprobados con decisiones y costos):
lector con horario, encabezado/pie configurables, búsqueda del tesoro con tarjetas,
listas de deseos compartibles sin precios, docentes y listas de material,
panel en módulos, correo con Brevo.

### Regla de trabajo durante la feria

**El viernes 6/11 no se toca nada.** Lector congelado desde el jueves.

---

## 11. Riesgos y deuda técnica

| # | Riesgo | Impacto | Estado |
|---|---|---|---|
| 1 | ~~No hay dump automático de la base~~ | Alto | **RESUELTO 03/11/2026**: timer diario con verificación de que el dump abre |
| 2 | El DNS del dominio principal (`rayuelalibros.com.ar`) está en la cuenta de Hostinger que administra un tercero | Medio | Rayuela tiene el dominio en NIC.ar: puede recuperar el control cambiando nameservers |
| 3 | El DNS de `rayuelalaplata.com.ar` está en una cuenta personal de Jorge | Medio | Respaldo: NIC.ar (titular Rayuela). Se puede migrar a una cuenta de Rayuela en 10 min |
| 4 | El bot de novedades manda desde un Gmail personal | Medio | Se resuelve con Brevo (en curso) |
| 5 | El lector depende del Bridge en vivo para precios | Medio | Con la réplica local (pendiente, ver backlog) deja de depender |
| 5b | El endpoint que usa el lector **no está documentado** (se descubrió probando los puestos de autoconsulta; sin soporte ni garantía de permanencia) | **Alto** | Migrar el lector a la API documentada y a la réplica local. Mientras tanto, es lo que hay: funciona y es de solo lectura |
| 6 | ~~Puerto 22 abierto en sshd~~ | Bajo | **RESUELTO 03/11/2026**: solo escucha 5186 |
| 7 | Nombre temporal `sslip.io` todavía activo | Bajo | Retirar cuando se confirme el uso en celulares |
| 8 | Netbook con hardware viejo (32 bits) y servicios de Jorge mezclados con Novedades | Bajo | Documentado; separación futura |
| 9 | La lista del lector se pierde al recargar | Bajo | Se resuelve en el módulo 1 |

---

## 12. Checklist de traspaso

Si Jorge deja de mantener esto, en este orden:

**Cuentas y accesos**
1. Transferir la cuenta de Cloudflare (o al menos el acceso al DNS) a Rayuela
2. Acceso al panel de DonWeb (VPS) con facturación a nombre de Rayuela
3. Confirmar quién tiene la Clave Fiscal de NIC.ar y los dominios a nombre de Rayuela
4. Acceso al panel de Hostinger del correo (no tocar; solo tener el acceso)
5. Cuenta de Brevo (cuando esté activa)
6. Entregar claves SSH (canal seguro) y **rotarlas**
7. Repositorios de GitHub: agregar a la persona como colaborador

**Conocimiento**
8. Leer este documento + `RAYUELA-BACKLOG.md` + `RAYUELA-REGLAS.md`
9. Leer `SERVIDOR-DESPLIEGUE-Y-TUNEL.md` (netbook y túnel)
10. Recorrer el runbook (§6) una vez con Jorge al lado

**Verificación final**
11. Correr las pruebas (§9)
12. Hacer un deploy de prueba en `prueba.` y uno real en producción
13. Restaurar un respaldo en un entorno aislado (probar que funciona)
14. Rotar todas las credenciales
15. Registrar en este documento quién quedó a cargo y desde qué fecha

---

## 13. Glosario

| Término | Significado |
|---|---|
| **VPS** | Servidor virtual privado (la máquina en DonWeb) |
| **nginx** | Servidor web que recibe el tráfico y lo deriva a la app |
| **systemd** | Sistema que arranca y vigila los servicios del servidor |
| **Let's Encrypt / certbot** | Certificados HTTPS gratis y su herramienta de renovación |
| **DNS / nameserver** | Sistema que traduce el nombre del dominio a la IP |
| **Cloudflare** | Proveedor de DNS (y opcionalmente proxy) |
| **Delegación** | Acción en NIC.ar de indicar qué nameservers administran el dominio |
| **Bridge** | Sistema de gestión de la librería (dueño de precios y stock) |
| **SQLite** | Base de datos en un solo archivo |
| **fail2ban** | Banea IPs que fallan repetidamente |
| **ufw** | Firewall del servidor |
| **staging / ambiente de prueba** | Copia aislada para probar sin riesgo |
| **snapshot** | Foto completa del servidor en un momento dado |
| **RPO / RTO** | Cuánta información puedo perder / cuánto tarda volver a andar |
| **PWA** | App web instalable en el celular (icono en pantalla de inicio) |
| **voucher** | Tarjeta/vale de pago que hoy se usa en el local y Bridge no contempla |

---

## Historial del documento

| Fecha | Cambio |
|---|---|
| 03/11/2026 | Primera versión completa, con inventario verificado en el servidor |

---

## 14 · Demo de tienda y canal de consulta (03/11/2026)
- [15 · Novedades en el VPS, sync rápida y tapas externas](#15--novedades-en-el-vps-sync-rápida-y-tapas-externas-04112026)

### 14.1 Demo de tienda (`demo.rayuelalaplata.com.ar`)

Prototipo de la tienda online, alimentado con datos reales de Bridge en **solo lectura**.

| Dato | Valor |
|---|---|
| URL | `https://demo.rayuelalaplata.com.ar` |
| Servicio | `rayuela-demo.service` (puerto 5052, usuario `rayuela`) |
| Código | `/opt/rayuela/demo` |
| Base | `/opt/rayuela/demo/catalogo.db` (SQLite, ~55 MB, 447.000 productos) |
| Caché | `tapas/<isbn>.jpg` y `fichas/<isbn>.json` (archivos, no base) |
| Repo | GitHub privado `rayuela-demo` |

**Cómo se alimenta** (`carga_rapida.py` y `metadatos.py`, solo GET):

- `articulos/precio/...` → 0,05 s por página de 100 → catálogo completo en ~35 min
- `articulos/stock/...` → idem
- `articulos/atributos/...` → **9,7 s por página** (título, autor, colección, temas): va de noche
- Ficha con tapa y sinopsis: `articulo/{isbn}`, 1,6 s, **bajo demanda** y cacheada en archivos

**Decisión de diseño**: la web **no escribe en la base del catálogo** (las fichas van a
archivos) para que el sincronizador pueda escribir sin bloquearla. Un intento de escribir en
ambos produjo `database is locked` en producción de prueba el 03/11.

**Regla de publicación** (decidida por Jorge): se listan solo títulos con stock; un ISBN
buscado exactamente aparece igual, marcado "a pedido".

### 14.2 Canal de consulta por Telegram

| Dato | Valor |
|---|---|
| Bot | `@RayuelaRepoBot_bot` |
| Credenciales | `/etc/rayuela/telegram.env` (permisos 600, solo root) |
| Chat autorizado | id `558061905` — los mensajes de otros chats se ignoran |
| Comandos | `/usr/local/bin/avisar`, `/usr/local/bin/preguntar`, `/usr/local/bin/leer-respuestas` |
| Estado | `/var/lib/rayuela-telegram.offset` (hasta dónde se leyó) |

Uso: el asistente manda avisos y preguntas con botones; lee las respuestas entre tarea y
tarea. **No se usa para secretos** (Telegram guarda los mensajes en la nube; no es cifrado
extremo a extremo).

---

## 15 · Novedades en el VPS, sync rápida y tapas externas (04/11/2026)

### 15.1 · Novedades ya no vive en la netbook

| Antes | Ahora |
|---|---|
| Netbook de casa + Tailscale Funnel (`net-casa.tailfb7a36.ts.net/novedades`) | **VPS** con dominio propio |
| Dependía de que la netbook estuviera encendida | No depende de ninguna PC del hogar |
| `/novedades` dentro del túnel | `https://novedades.rayuelalaplata.com.ar/` (certificado Let's Encrypt) |

- Código: `/opt/rayuela/novedades` (paquete `novedades/` + `venv` con Flask, bs4, openpyxl, Pillow, requests)
- Servicio: `rayuela-novedades.service` (usuario `rayuela`, puerto 5060)
- Entorno: `/etc/rayuela/novedades.env` (600 root). `NOVEDADES_PREFIJO` **vacío** (ya no hay prefijo)
- Datos migrados: `datos/novedades.db` (trabajos, cache, destinatarios), `datos/trabajos/`, `salida/`
- nginx: sitio `novedades` (proxy a 5060). La ruta vieja `ferias.rayuelalaplata.com.ar/novedades/`
  hace **301** al dominio nuevo
- **No hay cron ni timer**: los escaneos se lanzan a mano desde el panel (se verificó que tampoco
  había cron en la netbook ni reglas en Node-RED)
- La netbook quedó con el servicio **disabled** y una copia fría de los datos
- QR nuevo: `demo_tienda/Novedades-QR.png` y `Novedades-QR-hoja-A4.pdf` (el QR anterior apuntaba
  a la URL del túnel y quedó muerto)

### 15.2 · Sincronización rápida (producción no puede esperar al día siguiente)

`rayuela-demo-rapido.service` → `sincronizar_rapido.py --intervalo 1800` (cada 30 minutos).

- Estado: `sync_estado.rapido_desde` (formato `YYYY/MM/DD/HHMM`), con 2 minutos de margen
- Pide **sólo lo modificado desde esa marca**:
  - `articulos/precio/<desde>/<pag>` → `guardar_precios`
  - `articulos/atributos/<desde>/<pag>` → `guardar_atributos` (título/autor)
  - `articulos/stock/<desde>/<pag>` → `guardar_stock` (ventas, reservas, reposiciones)
  - `articulo/<codigo>/stock` para los códigos tocados (hasta 300 por vuelta)
- Tope de 200 páginas por listado y por vuelta, para no quedar colgado en un aluvión
- Ciclo medido: **7,8 s** con cambios normales (2 precios, 2 fichas, 238 stocks)
- **Botón "Traer cambios ahora"** en `/admin` → `POST /admin/sincronizar`, que lanza
  `sincronizar_rapido.py --una` con `subprocess.Popen` (no bloquea la página), escribe
  `/opt/rayuela/demo/sync_manual.log` y guarda `ajustes.sync_manual_pedida`
- El escaneo histórico de `metadatos.py` sigue con `--desde 1900/01/01/0000`: es un barrido, no
  compite con la vía rápida. **Pendiente**: darle modo incremental con marca horaria propia.

### 15.3 · Tapas externas (scraper de distribuidores)

- Entorno: `/opt/rayuela/tapas_externas/venv` (requests, beautifulsoup4, lxml, Pillow)
- Scraper: copia del paquete `novedades` (`sitios.py` con motores **zivals**, **yenny**, **sbs**)
- Script: `/opt/rayuela/demo/tapas_externas.py`
  - Candidatos: `publicable = 1 and stock > 0` sin tapa de Bridge ni externa, con reintento a los 30 días
  - Orden de sitios: SBS → Zivals → Yenny
  - **Valida el título** (≥60 % de las palabras del título de la base presentes en el del sitio);
    si no coincide, **descarta** la tapa (`resultado = titulo_distinto`)
  - Guarda `tapas/<isbn>.jpg` (redimensionada a 600 px, JPEG q85) y `meta/<isbn>.json`
    (sitio, título devuelto, fecha, bytes)
  - Estado: `estado.json`; registro: `registro.csv`
- Resultado de la medición (2.000 títulos sin tapa, 29 min):
  **51,8 % de cobertura en los que tienen stock**, 14,6 % en los que no.
  14 % de las tapas traídas se descartaron por título distinto. ~47 KB por tapa.
- Decisión: correr **sólo sobre los publicados con stock**. Los sin stock no se scrapean.
- La web resuelve `tapa_src()`: Bridge primero, externa después, nada al final.
  nginx sirve `/tapas/` y `/tapas-externas/` como estáticos con caché de 30 días.

### 15.4 · Otros cambios del 04/11

- **Curaduría**: `/admin/publicacion` permite ocultar títulos (`productos.oculto`) y marcarlos con ☆
  como recomendados del librero (`destacados`), que reemplazan a los aleatorios de la portada
- **Consultas**: formulario en la ficha → tabla `consultas` → aviso por Telegram
  (`rayuela-demo-consultas.timer`, cada 5 min) → `/admin/consultas`
- **Datos del local**: WhatsApp, dirección, horario y medios de pago desde el panel; se usan en el
  carrito ("cómo comprar") y en el pie
- **Subir lista** (`/lista`): resuelve listas de colegios/reposición comparando **sin acentos, por
  palabras en cualquier orden** y eligiendo el título más parecido; índice en memoria renovado
  cada 10 minutos; hasta 200 líneas por envío
- **Salud**: el chequeo ahora también controla la demo y Novedades, y valida el respaldo más
  reciente con menos de 30 h (antes pedía el archivo del día y daba falso positivo antes de las 03:10)
- **Bridge y concurrencia**: bajo carga devuelve respuestas vacías ("imagen": [""]) en vez de
  error. Todo trabajo que lo consulte debe tratar el vacío como "no hay dato" y, si importa,
  reintentar de a uno. Lección medida dos veces.

### 15.5 · Pendientes técnicos anotados

1. `metadatos.py` en modo incremental (marca horaria propia) para que los títulos nuevos no
   dependan del avance del barrido histórico.
2. Generar el ZIP de tapas de los más vendidos para cargar en Bridge (la herramienta ya existe
   en el scraper: `tapas.comprimir()`), cuando Verónica delegue la tarea.
3. Tapas de los títulos sin stock: no se hacen por ahora (cobertura 14,6 %).
4. Roles por persona en el panel (vendedor / repositor / admin) en lugar de una clave única.

### 15.6 · Cómo se suben los repos a GitHub (04/11/2026)

El entorno del asistente **no puede lanzar ssh desde git** (el sandbox del escritorio bloquea la
creación de tuberías: `sh.exe: couldn't create signal pipe`). Por eso el push se hace desde el VPS:

1. En la PC: `git bundle create <repo>.bundle --all`
2. `scp` del bundle al VPS
3. En el VPS: `git clone <repo>.bundle` y `git push origin --all` usando la deploy key
   `/root/.ssh/github_rayuela` (permisos 600, configurada como host `github-rayuela`)

La deploy key es **por repositorio** y necesita **"Allow write access"** en GitHub. Sin eso,
`git ls-remote` funciona pero `git push` responde "Please make sure you have the correct access
rights". Los repos locales quedan apuntando a HTTPS; el push se hace desde el VPS.

### 15.7 · Regla: priorizar que Bridge no se ralentice (04/11/2026)

**Instrucción de Jorge:** nunca hacerle perder velocidad al sistema que usa la librería en el
mostrador. Bridge comparte servidor con el POS, así que nuestros trabajos van en horario de
comercio cerrado y con pausas.

Medido el 04/11 a las 9 h (con varias cargas nuestras encima):
`articulos/atributos` pasó de 9,7 s a **28-30 s por página** y `articulos/precio` de 0,05 s a
0,8 s. Con los trabajos throttled el stock volvió a 55 ms.

Cómo quedó repartido:

| Trabajo | Horario | Ritmo |
|---|---|---|
| Sync rápida (precio, título, stock por fecha) | cada 30 min | 1 pasada corta (~8-35 s) |
| Stock completo de los publicados | **sólo de noche** (8-21 no corre) | pausa 0,25 s entre consultas |
| Fichas (sinopsis) | **sólo de noche**, ventana 21-8, timer 21:00 | 4 hilos, pausa 0,3 s, **tope 3.000 por noche** y 240 min |
| Metadatos históricos | corrida única | ya completada |
| Tapas de Bridge | cada 6 h | consultas livianas |
| Tapas externas | 03:40 | contra sitios de terceros, no Bridge |
| Consultas de clientes | cada 5 min | sólo SQLite |
| Salud | cada 30 min | 3 pedidos HTTP |
| Respaldo | 03:10 | local |

Protecciones en el trabajo de fichas (`fichas_nocturnas.py`):

- **guarda de horario**: fuera de 21-8 no hace nada
- **guarda de latencia**: mide Bridge antes de arrancar; si está lento espera 10 min y reintenta,
  y a la tercera aborta
- **topes**: 3.000 títulos y 240 minutos por corrida
- Prioriza **títulos con stock**, que son los que se muestran primero en la tienda

Si algún día hay que acelerar la carga, la palanca es el horario, no los hilos.

### 15.8 · Actualización progresiva también de día (04/11/2026)

**Instrucción de Jorge:** que no se corte la actualización durante el día, pero que avance despacio
para no ralentizar Bridge.

Cómo avanza cada cosa:

| Trabajo | De día (8-21) | De noche (21-8) |
|---|---|---|
| Sync rápida (precio, título, stock por fecha) | cada 30 min | cada 30 min |
| Stock de los publicados | **250 por pasada** cada 30 min, 1,5 s entre consultas | pasada completa, 0,25 s |
| Fichas / sinopsis | **150 por tanda** cada 2 h (9-19), 1 hilo, 2 s de pausa | 3.000 por noche, 21:00 |
| Tapas de Bridge | cada 6 h | cada 6 h |
| Tapas externas | — | 03:40 |

Guarda nueva de las fichas de día: antes de arrancar mide `articulo/{isbn}/stock` (normal ~50 ms).
**Si tarda más de 1 segundo, aborta la tanda** y espera a la próxima. De noche el techo es 3 s.

Así el catálogo sigue avanzando unas 15.000 fichas y 12.000 stocks por día sin que el mostrador lo note.

### 15.9 · Subir lista con lectura de PDF y foto (OCR) (04/11/2026)

La pantalla "Subir lista" pasó a **dos pasos**:

1. **Leer**: se pega el texto, se sube un `.txt`/`.csv`, un **PDF** o una **foto**.
2. **Revisar y corregir**: se muestra lo leído en un cuadro editable con el conteo de renglones.
   Después "Buscar en el catálogo".

En el resultado **cada línea es editable**: si el OCR leyó mal, se corrige ahí mismo y se vuelve a
buscar esa línea (botón o Enter) contra `/api/lista/linea`, sin recargar la página. También se
puede sacar una línea. Arriba se ve el resumen: disponibles · a pedido · no encontrados.

Dependencias instaladas en el VPS:

| Paquete | Para qué |
|---|---|
| `tesseract-ocr` + `tesseract-ocr-spa` | OCR en español de las fotos |
| `poppler-utils` (`pdftoppm`) | pasar a imagen los PDF escaneados |
| `pypdf` (en el venv de la demo) | leer el texto de los PDF |

Módulo: `demo_tienda/leer_lista.py`. Reglas y límites:

- PDF con texto → lectura directa (lo más preciso). PDF escaneado → se detecta y va a OCR
- Foto → se agranda a 1400 px de ancho, escala de grises y OCR (`--psm 6`)
- **Letra manuscrita no se promete**: se avisa en pantalla
- Hasta 200 renglones por envío y 15 páginas de PDF
- Se limpian numeraciones ("1)", "12-"), separadores de tabla y renglones basura

Probado con una imagen de prueba: leyó `EL ALEPH`, `MARTIN FIERRO`, `LA INVENCIÓN DE MOREL` y el
ISBN correctamente.

### 15.10 · Identidad visual: logo, favicon y vista previa al compartir

- **Logo**: `static/logo-rayuela.png` (228x80), extraído del sitio real; se usa en la cabecera
- **Favicon**: `static/favicon.svg` es el **mismo que declara rayuelalibros.com.ar** (cuadrado
  oscuro con la R), más `favicon-32.png` y `apple-touch-icon.png` generados desde el logo
- **Vista previa al compartir**: etiquetas `og:title`, `og:description`, `og:image` en todas las
  páginas; en la ficha del libro la imagen es **la tapa del libro** y el título incluye autor y
  precio. `static/og-rayuela.png` (1200x630) es la tarjeta genérica para la portada
- **Datos reales del local** cargados en `ajustes`: WhatsApp `5492215672000` y las dos sucursales
  (Plaza Italia 187 en La Plata, La Merced 423 en Ensenada). **Falta**: horario y medios de pago
  (los tiene que decir Verónica)

Nota de negocio (aclaración de Jorge, 04/11): **el libro tiene un precio único** (el de tapa).
No corresponde hablar de "sin recargo": los adicionales que existan son por servicios (envío,
despacho a transporte) o por forma de pago, y se muestran aparte, nunca sumados al precio del libro.

### 15.11 · Recomendaciones por contenido (Fase 2)

- `recomendados(codigo)`: mismo autor (5 puntos), mismos temas (3 por tema), misma coleccion (2),
  +1 si tiene stock. Tope 6, cacheado 10 minutos por libro.
- `recomendados_de_la_visita()`: toma los ultimos libros vistos por la sesion (tabla `eventos`) y
  arma "Segun lo que miraste" en la portada.
- Indices nuevos: `ix_prod_autor`, `ix_prod_coleccion`.
- La editorial no se usa todavia como señal porque `productos.marca`/`editorial` están vacías: la
  editorial sólo viene en la ficha completa (`articulos/{codigo}`) y se guarda en el cache de fichas.

### 15.12 · Incidente del 03/11 a la hora del cierre y salvaguardas nuevas

**Qué pasó.** El 03/11, entre las 18:58 y las 19:40 (justo en el cierre de caja de la librería),
el VPS hizo un pico de pedidos a Bridge:

| Trabajo | Ritmo medido | Nota |
|---|---|---|
| Tapas de Bridge | **37 pedidos por segundo** | Se había subido a 9 hilos a las 19:02 para acelerar la carga |
| Stock de publicados | **12,5 pedidos por segundo** | Pasada cada 5 minutos en ese momento |
| Fichas (sinopsis) | ~2,5 por segundo | 4 hilos pidiendo la ficha completa |
| Metadatos | 1 página cada ~6 minutos | pero cada página costaba 10-30 s del lado de Bridge |

Total: del orden de **45-50 pedidos por segundo sostenidos**, sin coordinación entre trabajos.
Eso explica la lentitud de los procesos de cierre. **La causa fue nuestra.**

**Qué se hizo.**

1. **Limitador global de ritmo** (`demo_tienda/limite.py`): una única cuota de **3 pedidos por
   segundo** compartida entre todos los procesos, con un archivo y `flock`
   (`/var/lock/rayuela-bridge-ritmo`, dueño `rayuela`). Probado con dos procesos en paralelo:
   12 turnos en 3,7 s → 3,3 por segundo combinados.
2. **Un solo trabajo contra Bridge a la vez**: todas las unidades tienen
   `flock -n /run/rayuela-bridge.lock`, así no se apilan dos cargas.
3. **Tapas**: de 9 hilos a **2 hilos con 0,4 s de pausa** (tope teórico ~4/s, recortado a 3 por el
   limitador).
4. **Stock**: pausa de 0,5 s y sólo de noche.
5. **Nada de Bridge en horario comercial** salvo lo imprescindible.

**Regla operativa para no repetirlo:** los trabajos masivos van de noche, con el limitador puesto,
y nunca se suben hilos para "ir más rápido". Si hay que acelerar algo, se amplía la ventana
horaria, no el paralelismo.

### 15.13 · Corte total de los trabajos automáticos (04/11, 11:20)

**Decisión de Jorge:** ningún proceso automático debe consultar Bridge. Lo único permitido es la
consulta puntual de la app de ferias, que la dispara una persona (el equivalente a la autoconsulta
en el local).

**Cómo quedó implementado (tres capas):**

1. **Las unidades ya no existen en systemd.** Los 8 servicios y 4 timers de carga se movieron a
   `/etc/rayuela/unidades-off/`. `systemctl start` responde *"Unit not found"*: no se pueden
   arrancar ni por error ni al reiniciar el servidor.
2. **Bandera de corte en el código.** Todos los scripts (`sincronizar.py`, `metadatos.py`,
   `stock_publicados.py`, `tapas_publicadas.py`, `fichas_publicadas.py`, `fichas_nocturnas.py`,
   `sincronizar_rapido.py`, `carga_stock.py`) chequean `/etc/rayuela/pausa-bridge` al arrancar y
   salen con el mensaje `CORTE: ... no se consulta Bridge.` Aunque alguien los ejecute a mano,
   no hacen nada.
3. **Pausa en la web.** `/opt/rayuela/demo/PAUSA_BRIDGE` impide que la tienda pida fichas.

**Qué sigue funcionando:** la tienda demo (con los datos ya descargados), la app de ferias y su
ambiente de prueba, y Novedades. **Qué no se actualiza:** precios, stock, títulos nuevos, tapas y
sinopsis, hasta que Jorge autorice reanudar.

**Para reanudar** (cuando Rayuela confirme que el servidor está normal): mover los archivos de
`/etc/rayuela/unidades-off` de vuelta a `/etc/systemd/system`, `systemctl daemon-reload`, borrar
`/etc/rayuela/pausa-bridge` y `/opt/rayuela/demo/PAUSA_BRIDGE`, y arrancar de a un trabajo por vez.

### 15.14 · Ajustes de diseño del 04/11 (sin tocar Bridge)

- "También te puede interesar" estaba mal ubicado: por un reemplazo de plantilla había quedado
  dentro del bloque de `<title>` y de las etiquetas `og:`, así que se dibujaba **arriba** de la
  ficha. Se reescribió `libro.html` y ahora cierra la página, después de la consulta.
- La sección pasó a **carrusel horizontal** (scroll con snap, sin flechas): 12 recomendados, cada
  tarjeta 150 px en escritorio y 132 px en celular, con barra de desplazamiento fina.
- Se pueden hacer cambios de diseño y de datos locales **sin consultar Bridge**: la tienda usa la
  base del catálogo y los archivos de `tapas/` y `fichas/` que ya están en el VPS.

### 15.15 · Busqueda con filtros e indice de texto (04/11)

**Filtros** en `/buscar`:
- **Editorial** (usa `productos.marca`, ya completada para 41.455 titulos) y **temas** (de `temas`),
  con las cantidades al lado.
- **Solo con stock**, **orden** por relevancia / menor precio / mayor precio / titulo / ultimos
  ingresados, y chips de los filtros activos para quitarlos uno por uno.
- Las facetas se calculan solo cuando la busqueda devuelve mas de 20 resultados (si no, son ruido).
- Resultado completo cacheado 5 minutos (los datos estan congelados: no cambian).

**Indice de texto (FTS5)** para que la busqueda no recorra las 428 mil filas con `LIKE %texto%`:
- `indexar_busqueda.py` crea `buscar_fts` (titulos publicables: descripcion + autor + marca + temas),
  con `remove_diacritics 2` para que "anos" encuentre "AÑOS" y al reves.
- La busqueda principal y la instantanea (`/api/buscar`, la que corre al tipear) usan el indice.
- **Si el indice no existe o falla, cae automaticamente al `LIKE` de antes**: nada se rompe.
- Medido: `/buscar` 0,06-0,26 s (antes 0,63-0,77 s) · `/api/buscar` 0,04-0,06 s (antes ~0,3 s).

**Importante:** al reanudar las sincronizaciones hay que volver a correr
`/opt/rayuela/ferias/venv/bin/python /opt/rayuela/demo/indexar_busqueda.py` para que el indice
incluya los cambios (tarda 3 segundos).

### 15.16 · Diseño: esqueletos, estados vacíos y página institucional (04/11)

- **Esqueletos**: mientras la búsqueda instantánea consulta, se muestran tres barras con brillo y el
  texto "Buscando “x”…" en lugar de una caja vacía. Las tapas entran con un fundido de 0,35 s
  (`.tapa img` arranca en opacidad 0 y se marca `cargada` al terminar de cargar).
- **Botones con espera**: los formularios marcados con `data-espera` (consulta de la ficha y subir
  lista) bloquean el botón y muestran "Un segundo…" hasta que termina el envío.
- **Estados vacíos** con salida concreta: carrito ("Buscar un libro" / "Subir una lista"),
  búsqueda sin resultados (WhatsApp + subir lista) y resultado de lista sin ningún disponible
  (consultar por WhatsApp / probar otra lista).
- **Página institucional** `/nosotros`: sucursales (Plaza Italia 187 y La Merced 423), cómo comprar
  en tres pasos, qué se encuentra en la tienda y consultas. Linkeada desde el pie de todas las
  páginas. **No inventa horarios ni formas de pago**: eso falta que lo diga Verónica.

### 15.17 · Panel: aviso del estado del catálogo (04/11)

El panel (`/admin`) muestra arriba de todo:

> **Estado del catálogo** · Datos del sistema al **04/11/2026 10:25** · **actualización pausada**
> (a pedido de la librería) · Precios y stock pueden haber cambiado después de esa fecha.

La fecha sale de `max(productos.actualizado)`, que la base guarda en **UTC**; se muestra convertida
a hora de Argentina (UTC-3) para no confundir a quien la lea. El aviso de "actualización pausada"
aparece sólo si existe la bandera `PAUSA_BRIDGE`.

También se corrigió la tabla del resultado de listas: en celular se desplaza horizontalmente en vez
de desbordar la pantalla.

### 15.18 · Búsqueda tolerante a errores de tipeo (04/11)

Cuando la búsqueda no encuentra nada, el sistema corrige las palabras contra el **vocabulario del
catálogo** y muestra: *"No encontramos nada para «borgs». ¿Quisiste decir **borges**?"*, con los
resultados de la palabra corregida.

- `indexar_palabras.py` arma la tabla `palabras` (65.478 palabras con 2 o más apariciones) a partir
  del índice de texto. Tarda 4 segundos.
- La corrección usa `difflib.get_close_matches` sobre las palabras del catálogo que empiezan con la
  misma letra y tienen un largo parecido (tope 6.000 candidatas). Detecta letras cambiadas,
  faltantes, sobrantes y **transposiciones en el medio** ("alehp" → "aleph").
- Se aplica sólo cuando la búsqueda exacta da cero resultados, así que no afecta las búsquedas que
  ya funcionan (verificado: "borges" sigue dando 395 y no muestra aviso).
- Funciona en la página de resultados y en la búsqueda al tipear.
- **Al reanudar la sincronización hay que correr `indexar_busqueda.py` y después
  `indexar_palabras.py`.**

Medición: 10 errores de tipeo reales, 9 resueltos con la palabra correcta. "coratza" propuso
"corteza" en lugar de "cortazar" (limitación del umbral de similitud).
