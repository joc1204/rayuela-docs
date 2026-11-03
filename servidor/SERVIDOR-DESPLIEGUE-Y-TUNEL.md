# Servidor domotica-bangho: cómo desplegar una app y publicarla en internet sin romper las que ya andan

> **Leé esto antes de tocar el servidor, desplegar una app o publicar algo en el túnel.**
>
> Este documento existe porque ya hubo un incidente: el túnel de Tailscale se cayó
> y costó horas encontrarlo, porque el servidor *parecía* estar bien. Acá está lo
> que hay que saber para no repetirlo.

---

## 1. El servidor

- Netbook `domotica-bangho`, Debian 32 bits, LAN `192.168.1.19`
- Corre como usuario **`jorge`**
- **`jorge` NO está en sudoers** (`sudo` responde "jorge is not in the sudoers file").
- **Para tareas de root se usa `su -`** y la contraseña de root:

  ```bash
  su -
  # ahora sos root: el prompt pasa a root@domotica-bangho:~#
  ```

  Todo lo que vaya a `/usr/local/bin`, `/etc` o systemd se hace así.

> En este documento, **donde diga `sudo`, hacelo como root vía `su -`.**

### Cómo entrar

```bash
ssh -i .ssh_keys/id_rsa \
    -o BatchMode=yes \
    -o StrictHostKeyChecking=no \
    -o UserKnownHostsFile=.ssh_keys/known_hosts \
    jorge@192.168.1.19
```

Las claves están en `.ssh_keys/` del workspace.

> **Cambio de módem — 26/10/2026:** el módem nuevo movió la LAN de `192.168.0.x` a `192.168.1.x`.
> La netbook quedó en **`192.168.1.19`** (gateway `192.168.1.1`). No cambió nada más: ni la
> tailnet ni el Funnel, la URL pública sigue siendo la misma.
>
> Si volvés a cambiar de red, o no sabés en qué segmento está la netbook, entrá por **Tailscale**:
> funciona desde cualquier red y no depende del módem.
>
> ```bash
> ssh -i .ssh_keys/id_rsa jorge@100.92.248.2   # IP de la netbook en la tailnet (100.x)
> ```

### Qué corre hoy

| Servicio | Puerto | Publicado en |
|---|---|---|
| `gastos.service` (Flask) | 5000 | `/gastos` |
| Node-RED | 1880 | `/app` |
| `presupuestito.service` (Flask) | 5001 | `/presupuestos` |
| `ferias` (otra app, fuera de este sistema) | 5050 | `/ferias` |
| `rayuela-novedades.service` (Flask) | 5060 | `/novedades` |

---

## 2. El túnel (Tailscale Funnel)

- Host público: **`net-casa.tailfb7a36.ts.net`**
- IPs de ingreso: `209.177.145.97`, `209.177.145.192`

### Los puestos viven en un archivo, no en el código

```
/etc/tunel-apps.conf
```

Formato: `<path> <destino>`

```
/app     http://127.0.0.1:1880/app
/gastos  5000
/novedades  5060
```

**Para publicar una app nueva alcanza con agregar una línea ahí.** Antes los
puestos estaban escritos dentro del vigilante, y eso era una trampa (punto 3).

---

## 3. Las tres trampas

> **Actualización 2026-10-17:** al publicar una tercera app (`presupuestito`, en `/presupuestos`)
> aparecieron **dos trampas nuevas** que no están en esta sección: el funnel **recorta el prefijo**
> y el vigilante **no detecta** un puesto faltante. Están documentadas en la **sección 8**, con la
> receta corregida para publicar puestos nuevos. Leer las dos cosas antes de agregar una app.

### ⚠️ Trampa 1: `tailscale funnel --set-path` puede tumbar TODO el túnel

Es el comando que se usa para agregar un puesto, y es el que causó el incidente.

- Bug de Tailscale: <https://github.com/tailscale/tailscale/issues/19508>
  El daemon solo empuja el estado del funnel al plano de control **al arrancar**.
- Hilo con el arreglo: <https://github.com/tailscale/tailscale/issues/7103>

**Síntoma engañoso:** `tailscale funnel status` muestra todo bien en el equipo,
pero desde internet el nombre no resuelve o da error.

**Recuperación (esta funcionó):**

```bash
tailscale funnel --https=443 off
# volver a publicar TODOS los puestos de /etc/tunel-apps.conf
tailscale funnel --bg --set-path /app "http://127.0.0.1:1880/app"
tailscale funnel --bg --set-path /gastos "5000"
```

Última opción: `tailscale down && tailscale up`

### 🔴 Trampa 2: el vigilante reescribe la configuración completa

`/usr/local/bin/funnel-check.sh` corre cada **30 minutos**. Si detecta que el
túnel no está publicado, lo reconstruye desde `/etc/tunel-apps.conf`.

- **Versión nueva (la instalada):** lee los puestos del archivo, así que respeta
  cualquier app que se haya agregado.
- **Versión vieja:** tenía `/app` y `/gastos` escritos adentro. Al reparar,
  **borraba los paths que no conocía.** Por eso se cambió.

> Si alguna vez hay que reinstalar, usar `actualizar_funnel_check.sh`, NO el
> instalador viejo.

Log: `/var/log/funnel-check.log`

### 🔴 Trampa 3: el servidor se miente sobre su propio túnel

Desde el propio netbook, `curl https://net-casa.tailfb7a36.ts.net/gastos/`
**resuelve por MagicDNS a la IP interna** y devuelve `200` aunque el túnel esté
roto. Ese 200 es falso.

**Verificación externa real** — que un proxy de afuera busque la URL:

```bash
bash gastos_app/verificar_externo.sh
```

El script hace dos cosas para que el chequeo sea honesto:

1. Consulta a través de **r.jina.ai**, que busca la URL desde sus propios
   servidores (no desde el netbook).
2. Agrega un **cache-buster** (`?_cb=<timestamp>`) y el header `x-no-cache`,
   porque **r.jina.ai cachea**: sin eso un `200` puede ser una respuesta vieja.

Da `OK` con el título de la página si está vivo. Si no, es porque está roto.

---

## 4. Cómo publicar una app nueva en el túnel

1. La app tiene que estar escuchando en un puerto local (`127.0.0.1:PUERTO`).
2. Agregar la línea en `/etc/tunel-apps.conf`:
   ```
   /mi-app   5001
   ```
3. `systemctl restart funnel-check.timer` (como root)
4. **Verificar desde afuera** con el truco de r.jina.ai (trampa 3).
5. Verificar también que **las apps que ya estaban sigan funcionando**.
6. Confirmar que quedó escrita: `cat /etc/tunel-apps.conf`

---

## 5. Cómo desplegar la app de gastos

```bash
# 1) copiar los archivos
scp -i .ssh_keys/id_rsa <archivos> jorge@192.168.1.19:/home/jorge/proyectos/gastos_app/

# 2) reiniciar
pkill -TERM -f 'gastos_app/[a]pp.py'
```

> **El backend NO toma el código nuevo solo.**
> El frontend (HTML/JS/CSS) se sirve del disco y se actualiza al instante, pero
> `app.py` necesita el reinicio. Ya pasó una vez: el frontend mostraba funciones
> nuevas mientras el backend corría código viejo, y una tabla nueva no existía.
>
> **Verificar siempre después de desplegar.**

### Verificación completa

```bash
bash /tmp/final_v2.sh
```

Hace reinicio, chequeo de tablas, rutas del backend, suites de prueba, camino
público y elementos del frontend. El script está en `gastos_app/final_v2.sh` y
en el workspace.

### Migraciones

`init_db()` corre al arrancar y es idempotente. **Respaldar antes:**

```bash
cp gastos.db gastos.db.antes-<algo>
```

---

## 6. Secretos

- `gastos_app/secreto.key` — clave de sesión de Flask (64 hex, modo 600)
- Nunca commitear, mover ni copiar ese archivo fuera del servidor

---

## 7. Comandos de diagnóstico rápido

```bash
tailscale status | head -3
tailscale funnel status
systemctl is-active gastos.service funnel-check.timer
systemctl list-timers funnel-check.timer --no-pager | head -2
tail -5 /var/log/funnel-check.log
ss -tlnp | grep -E ':5000|:1880|:PUERTO_NUEVO'
```

---

## 8. Agregado 2026-10-17 — Publicar una tercera app: dos trampas NUEVAS

> **Por qué está esta sección.** El 17/10/2026 se publicó `presupuestito` en `/presupuestos`
> (puerto 5001). Con el procedimiento de la sección 4, el túnel devolvió 404 desde afuera y costó
> un buen rato encontrar por qué. Aparecieron dos causas nuevas que no estaban documentadas acá.
> Esta sección se agrega (no reemplaza nada) para que la próxima lectura vaya directo al grano.

### 8.1 Trampa 4 (nueva): Tailscale Funnel RECORTA el prefijo

`tailscale funnel --set-path /presupuestos 5001` publica la ruta, pero **antes de reenviar a la
app le borra el prefijo**: una request a `https://.../presupuestos/login` llega a Flask como
`/login`.

Consecuencia: si la app genera links absolutos con `url_for()` sin prefijo, todos sus enlaces
(`href`, `action`, `/static/...`) salen **sin** `/presupuestos`; el navegador pide
`https://.../login` a secas, el relay no conoce esa ruta y devuelve la 404 plana de Tailscale. La
app "parece" caída cuando en realidad está perfecta.

Cómo se resuelve (así lo hace `presupuestito/app.py`):

1. `SCRIPT_NAME` se fija **siempre** al prefijo en el middleware (`PrefijoProxy`), aunque el
   prefijo no venga en el path. Así `url_for()` genera `/presupuestos/...` y el funnel lo recorta
   de vuelta. Funciona tanto si el funnel recorta como si no.
2. **Ninguna ruta interna puede empezar con el mismo texto que el prefijo.** Presupuestito se
   publica en `/presupuestos`, así que sus rutas internas son `/lista`, `/nuevo`, `/<id>`,
   `/<id>/enviar`, etc. Antes eran `/presupuestos/...` y chocaban: al recortar el funnel, la app
   confundía la ruta interna con la raíz del montaje (daba 301 o 404).
3. La otra estrategia posible es usar **rutas relativas** en el HTML (como hace `gastos`:
   `static/style.css` en vez de `/gastos/static/...`). Cualquiera de las dos sirve; elegir una y
   verificarla desde afuera.

### 8.2 Trampa 5 (nueva): el vigilante NO detecta un puesto que falta (falso positivo)

El vigilante `funnel-check.sh` decide si reconstruir el funnel mirando desde el netbook:

```bash
curl -s -o /dev/null --max-time 15 "https://$HOST$path/"
```

Ese `curl` **no usa `-f`**, así que devuelve éxito ante cualquier respuesta, incluida una 404.
Sumado a que por MagicDNS el nombre resuelve a la IP interna, `publicados_todos()` da `OK` casi
siempre y el vigilante concluye "está todo bien" aunque el plano de control de Tailscale no
conozca la ruta nueva.

Evidencia real de ese día: después de agregar `/presupuestos 5001` al archivo, el log decía
`OK: el funnel esta publicado y funcionando (3 puesto/s)`, `tailscale funnel status` mostraba 3
puestos, y **desde internet `/presupuestos/` daba 404**. El log cuenta los puestos del archivo,
no los que el relay conoce.

**Regla:** después de agregar una línea a `/etc/tunel-apps.conf`, el vigilante no alcanza. Hay que
re-publicar el funnel a mano y verificar desde afuera (ver 8.3).

### 8.3 Receta actualizada para publicar un puesto nuevo

Esto corrige el paso 3 de la sección 4 (`systemctl restart funnel-check.timer` no dispara la
publicación; y aunque corra el servicio, el falso positivo de 8.2 lo deja pasar):

```bash
# 1) como root: agregar la línea a /etc/tunel-apps.conf    (ej: /presupuestos  5001)
# 2) como root: re-publicar TODO leyendo el archivo (la recuperación de la trampa 1)
bash /home/jorge/presupuestos/instalacion/republicar_funnel_como_root.sh
# 3) verificar desde afuera con título esperado, el puesto nuevo Y los viejos
bash /home/jorge/presupuestos/instalacion/verificar_afuera.sh
```

`republicar_funnel_como_root.sh` hace `tailscale funnel --https=443 off` y vuelve a publicar todos
los puestos de `/etc/tunel-apps.conf` con `--set-path`. Es idempotente, no toca el archivo de
configuración y verifica por r.jina.ai. El túnel se corta ~30-40 segundos mientras republica.

`reparar_tunel_como_root.sh` (misma carpeta) es para el caso más grave: reinicia `tailscaled` para
forzar el push del estado al plano de control y después asegura los puestos. **En este caso no hizo
falta**: se usó primero porque el síntoma parecía la trampa 1 pura.

> **Nota 2026-10-28 (verificador con falso negativo).** Al publicar `/novedades`, el paso 3 de este
> script reportó `FALLA /gastos/` **aunque `/gastos/` respondía bien**: en el mismo bloque imprimió
> el título real (`Cuenta Clara · Administración económica`) y el HTML del login. La publicación era
> correcta (los cinco puestos figuraban en `tailscale funnel status` y los cinco respondían desde
> afuera). Conclusión: **un `FALLA` de ese verificador en un puesto que ya existía no siempre es
> real** — comparar con la verificación honesta de la sección 8.4 antes de "reparar" nada.

### 8.4 Cómo saber si un 404 es del túnel o de la app

No son iguales, y confundirlos cuesta tiempo:

- **404 de Tailscale**: página plana `404 page not found`; cuando se mira por r.jina.ai aparece
  `Title:` vacío. El relay no conoce la ruta, o la app redirigió a una ruta sin prefijo.
- **404 de la app**: es HTML nuestro (en Presupuestito, `404 · Presupuestito`).

Chequeo honesto sin depender de r.jina.ai (desde el netbook, salteando MagicDNS con la IP del
relay público):

```bash
IP=$(dig +short net-casa.tailfb7a36.ts.net @8.8.8.8 | tail -1)   # IP pública del relay
curl -s -o /dev/null -w '%{http_code}\n' \
  --resolve "net-casa.tailfb7a36.ts.net:443:$IP" \
  "https://net-casa.tailfb7a36.ts.net/presupuestos/login"
```

Y para saber si la app recibe el prefijo o el funnel lo recortó, mirar los links del HTML servido:

```bash
curl -s --resolve "net-casa.tailfb7a36.ts.net:443:$IP" \
  "https://net-casa.tailfb7a36.ts.net/presupuestos/login" | grep -oE 'action="[^"]*"|href="[^"]*"'
```

Si aparece `action="/login"` (sin prefijo), el funnel recortó y la app no lo está compensando.

**Corolario para la verificación externa:** no basta con que r.jina.ai devuelva *algún* `Title:`.
Hay que comparar el **título esperado** (ej. `Ingresar · Presupuestito`), porque un 404 del relay
también "responde algo". Por eso los scripts de verificación validan contenido, no solo que exista
respuesta.

### 8.5 Mapa de Presupuestito (tercera app del servidor)

| Dato | Valor |
|---|---|
| URL pública | `https://net-casa.tailfb7a36.ts.net/presupuestos/` |
| Línea en `/etc/tunel-apps.conf` | `/presupuestos  5001` |
| Puerto / bind | `127.0.0.1:5001` |
| Servicio | `presupuestito.service` (User=jorge, Restart=always) |
| Código | `/home/jorge/presupuestos` (app `app.py`, base `presupuestito.db`, secreto `secreto.key`) |
| venv | `/home/jorge/presupuestos/venv` |
| Variables | `PRESPUESTITO_PREFIJO=/presupuestos`, `PRESPUESTITO_PUERTO=5001`, `PRESPUESTITO_HOST=127.0.0.1`, `PRESPUESTITO_SECURE=1`, `PRESPUESTITO_URL_PUBLICA=https://net-casa.tailfb7a36.ts.net/presupuestos` |
| Verificación | `bash /home/jorge/presupuestos/instalacion/verificar_afuera.sh` |
| Pruebas | `cd /home/jorge/presupuestos && ./venv/bin/python -m unittest discover -s tests` |

Rutas internas (son las que ve la app después del recorte del prefijo): `/`, `/login`,
`/registro`, `/lista`, `/nuevo`, `/<id>`, `/<id>/editar|enviar|aceptar|rechazar|anular|duplicar|renovar|imprimir`,
`/catalogo`, `/clientes`, `/radar`, `/cuenta`, `/p/<token>` (link público del presupuesto),
`/salud`, `/robots.txt`.

Desplegar / actualizar como jorge:

```bash
bash /home/jorge/presupuestos/instalacion/desplegar_como_jorge.sh   # venv + deps + pruebas + humo
```

Instalar o reinstalar como root (servicio + puesto en el túnel + verificación):

```bash
su -
bash /home/jorge/presupuestos/instalacion/instalar_como_root.sh
```

Reiniciar la app sin root (el servicio tiene `Restart=always`, la levanta systemd en ~5 s):

```bash
pkill -TERM -f 'presupuestos/[a]pp.py'
```

> Ojo con `pkill -f`: si el patrón coincide con la propia línea de comando del shell remoto, se
> mata a sí mismo y no ves la salida. Por eso el patrón va con corchetes (`[a]pp.py`), igual que
> el `gastos_app/[a]pp.py` de la sección 5.

### 8.6 Pendientes detectados (no resueltos todavía)

- El chequeo del vigilante debería usar `curl -sf` para fallar ante 404 (hoy da falso positivo y
  no detecta rutas nuevas). Si se toca `/usr/local/bin/funnel-check.sh`: respaldar antes y probar
  una corrida a mano.
- Los respaldos de `presupuestito.db` son locales (mismo disco): falta copia externa.
- El netbook se apaga de noche y no es hosting de producción. Para cobrar suscripciones, migrar a
  VPS + dominio propio (la app ya está preparada: todo se configura por variables de entorno).

---

## 9. Chequeo de salud — `verificar_netbook.sh` (agregado 2026-10-26)

**Qué es.** Un script bash que responde en un comando "¿está todo bien?" después de un reinicio,
un cambio de red (como el del módem del 26/10/2026) o un deploy. Cubre las apps **y** el túnel.

**Dónde vive.** En el workspace, en la raíz, junto a este documento (`verificar_netbook.sh`).
**No está instalado en el servidor**: se copia a `/tmp`, se ejecuta y se borra. No requiere root.

**Naturaleza: solo lectura.** No reinicia servicios, no toca configuración, no publica nada.
Lo único que escribe es `/tmp/.verificar_netbook.html` y lo borra al salir (`trap ... EXIT`).

**Qué verifica** (24 chequeos en 7 bloques):

1. **Red y entorno**: IP de LAN, IP de Tailscale, gateway, uso de disco y memoria disponible.
2. **Tailscale y Funnel**: `tailscaled` activo, host público del funnel.
3. **Puestos: archivo vs. relay** — compara cada línea de `/etc/tunel-apps.conf` contra lo que
   `tailscale funnel status` dice que el relay publica. Detecta la **trampa 5** (el archivo lista
   un puesto que el plano de control no conoce).
4. **Servicios**: `gastos.service`, `presupuestito.service`, `rayuela-novedades.service`,
   `funnel-check.timer`, proceso de Node-RED y próximo disparo del vigilante.
5. **Puertos**: deduce el puerto de cada destino en `/etc/tunel-apps.conf` y comprueba que escuche.
6. **Verificación externa honesta** (**trampa 3**): resuelve el nombre contra `8.8.8.8` (no
   MagicDNS) y consulta `https://<host><puesto>` con `curl --resolve -L`, esperando `200` y el
   título esperado. Los puestos que son sólo prefijo sin página propia (ej. `/app`) se sondean en
   una página real (`/app/pendientes`); sin eso dan un falso 404.
7. **API de la Mini App**: sin firma de Telegram, `/app/api/pendientes` debe devolver `401`
   (prueba que el endpoint existe y que la validación actúa).

**Cómo se corre** (desde el workspace, en Windows):

```bash
scp -i .ssh_keys/id_rsa verificar_netbook.sh jorge@192.168.1.19:/tmp/
ssh -i .ssh_keys/id_rsa jorge@192.168.1.19 "bash /tmp/verificar_netbook.sh"
```

Con `--local` saltea el bloque 6 (útil si no hay internet).

**Salida.** Una línea por chequeo: `[ OK  ]`, `[AVISO]` o `[FALLA]`, y un resumen
`OK: n · AVISOS: n · FALLAS: n` con `RESULTADO: todo en orden`. Código de salida `0` si no hay
fallas, `1` si hay al menos una.

**Cómo interpretar un resultado** (reglas para una IA o para quien lea la salida):

| Salida | Significa | Qué hacer |
|---|---|---|
| `[FALLA] … 404 del relay` | El plano de control de Tailscale no conoce la ruta | Republicar el funnel (sección 8.3) |
| `[FALLA] … 404 de la app` | El relay la conoce, la app no tiene página ahí | Revisar la ruta o el deploy de esa app |
| `[FALLA] el relay NO publica X` | El archivo y el relay discrepan (trampa 5) | Republicar y volver a correr el chequeo |
| `[FALLA] puerto N NO escucha` | El servicio de esa app está caído | `systemctl status` del `.service`; reiniciar como jorge o root |
| `[AVISO] título no esperado` | La app responde pero la página cambió | Verificar a mano que sea la página correcta |
| `[AVISO] memoria disponible baja` | Menos de 80 MB libres | Revisar procesos; el netbook tiene ~2 GB |

**Límites conocidos.** No valida el camino autenticado (login, tomar pedido, facturar): sólo
comprueba que la API rechace sin firma. El chequeo externo sale por el mismo enlace de internet de
la casa, así que confirma que el relay responde, no que un tercero cualquiera llegue.



---

## 10. La app de Novedades (`/novedades`, puerto 5060) — agregado 2026-10-28

**Qué es.** App de celular para cargar ISBN escaneando: arma la planilla de datos + tapas de las
librerías (Zennys, SBS, Zivals) y la manda por mail. Es el reemplazo del scraper de Streamlit.

| Dato | Valor |
|---|---|
| URL pública | `https://net-casa.tailfb7a36.ts.net/novedades` |
| Línea en `/etc/tunel-apps.conf` | `/novedades  5060` |
| Puerto / bind | `127.0.0.1:5060` |
| Servicio | `rayuela-novedades.service` (User=jorge, Restart=always, enabled) |
| Código | `/home/jorge/rayuela_scrapping` (paquete `novedades/`, base `datos/novedades.db`) |
| venv | `/home/jorge/rayuela_scrapping/.venv` (Flask, requests, bs4, openpyxl, Pillow) |
| Variables | `/home/jorge/rayuela_scrapping/servicio/.env` (se lee sola al arrancar) |
| Mail | SMTP de Gmail con clave de aplicación (la misma que usa `gastos_app/.smtp`) |
| Verificación | `curl -s 127.0.0.1:5060/salud` → `{"ok":true,"app":"novedades","mail":true}` |
| Pruebas | `cd /home/jorge/rayuela_scrapping && .venv/bin/python tests/test_sitios.py` (y `test_isbn.py`, `test_web.py`) |

Rutas internas (después del recorte del prefijo — cumplen la trampa 4: ninguna empieza con
"novedades"): `/`, `/ingresar`, `/salir`, `/salud`, `/api/trabajo`, `/api/trabajo/<id>`,
`/api/casillas`, `/api/casillas/<id>/borrar`, `/descargar/<id>/xlsx|csv|zip`.

**Datos que guarda** (todo bajo `/home/jorge/rayuela_scrapping/datos/`):

- `novedades.db` — trabajos (con `hechos` para el progreso), caché de ISBN por 24 h y casillas
- `trabajos/<id>/` — planilla xlsx, csv, tapas y zip de cada envío (se borran solos a los 30 días)
- `secreto.key` — firma de la sesión (modo 600, no copiar fuera del servidor)

**Probar un envío sin el celular** (como jorge):

```bash
cd /home/jorge/rayuela_scrapping && . .venv/bin/activate
python - <<'PY'
from novedades import trabajos
trabajos.inicializar()
id_t = trabajos.crear('Prueba', 'destino@ejemplo.com', ['9789871374991'])
print('procesado:', trabajos.procesar(id_t), '| estado:', trabajos.traer(id_t)['estado'])
PY
```

**Ver los últimos envíos:**

```bash
cd /home/jorge/rayuela_scrapping && . .venv/bin/activate
python - <<'PY'
from novedades import trabajos
with trabajos.conectar() as con:
    for f in con.execute('select id,estado,quien,cantidad,hechos,creado,cuando from trabajos order by creado desc limit 8'):
        print(dict(f))
PY
```

**Reiniciar** (el código Python nuevo NO se toma solo):

```bash
su -   # luego:  systemctl restart rayuela-novedades
```

**Si no llegan los mails:** el trabajo queda `listo` cuando Gmail aceptó el mensaje; si el trabajo
dice `listo` y no llegó, mirar Spam y que la casilla de destino exista (un destino inventado rebota
al remitente). La cuenta que envía es la de `NOVEDADES_SMTP_USUARIO`.

**Nota.** Usa el servidor de desarrollo de Flask (avisa "development server" en el log). Con 2-3
personas alcanza; si algún día hay concurrencia real, cambiar a `waitress` es una línea.