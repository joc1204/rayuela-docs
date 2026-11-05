# Infraestructura del VPS — mapa y reconstrucción

**Máquina:** VPS DonWeb · Ubuntu 24.04 · 2 vCPU · 2 GB RAM · 14 GB disco
**IP:** 201.32.132.197 · SSH puerto 5186, sólo con clave
**Zona:** America/Argentina/Buenos_Aires

> Este documento **no contiene secretos**. Las claves y tokens están en `estado/SECRETOS.md`
> (inventario) y se guardan en el gestor de contraseñas de Jorge.

## Qué corre acá

| App | Ruta | Puerto | Servicio | Dominio |
|---|---|---|---|---|
| Demo de tienda | `/opt/rayuela/demo` | 5052 | `rayuela-demo` | `demo.rayuelalaplata.com.ar` |
| Ferias + Lector | `/opt/rayuela/ferias` | 5050 | `ferias` | `ferias.` y `lector.rayuelalaplata.com.ar` |
| Ferias prueba | `/opt/rayuela/prueba` | 5051 | `ferias-prueba` | `prueba.rayuelalaplata.com.ar` |
| Novedades (scraping) | `/opt/rayuela/novedades` | 5060 | `rayuela-novedades` | `novedades.rayuelalaplata.com.ar` |

## Tareas programadas

| Unidad | Cuándo | Qué hace |
|---|---|---|
| `rayuela-demo-consultas.timer` | cada 5 min | avisa por Telegram las consultas nuevas de la demo |
| `rayuela-salud.timer` | cada 30 min | chequea que las apps respondan; avisa si no |
| `rayuela-respaldo.timer` | 03:10 | respaldo local (base de ferias, catálogo, configuración) |
| `rayuela-demo-*` (carga) | **archivadas** | actualización de Bridge: detenidas desde el 04/11 |

Las unidades de carga están en `/etc/rayuela/unidades-off/` (fuera de systemd) y este repo las
guarda en `units/` para cuando se reactiven.

## Datos en disco

| Qué | Tamaño | ¿Respaldo? |
|---|---|---|
| `demo/catalogo.db` | 139 MB | sí (`/var/backups/rayuela/catalogo-*.db.gz`) |
| `demo/fichas/` | 265 MB | **no** |
| `demo/tapas/` | 1,2 GB | **no** |
| `tapas_externas/` | 253 MB | **no** |
| `ferias/ferias.db` | pequeño | sí |

Los respaldos locales viven en `/var/backups/rayuela` (retención 14 días). **Siguen en el mismo
disco**: no protegen de perder el VPS. El respaldo externo está pendiente (ver `PENDIENTES.md`).

## Piezas de configuración versionadas acá

```
units/      unidades systemd (aplicaciones, timers y las de carga archivadas)
nginx/      sitios de nginx (demo, ferias, lector, prueba, novedades)
bin/        scripts propios (/usr/local/bin): avisar, preguntar, leer-telegram,
            leer-respuestas, rayuela-respaldo.sh, subir-repo
env-ejemplos/  plantillas de los archivos de /etc/rayuela (sin valores)
```

## Reconstruir desde cero (resumen)

1. **Base del sistema:** Ubuntu 24.04, usuario `rayuela`, `/opt/rayuela`, `/etc/rayuela`.
2. **Paquetes:** nginx, certbot (python3-certbot-nginx), fail2ban, sqlite3, tesseract-ocr,
   tesseract-ocr-spa, poppler-utils, python3-venv.
3. **Venvs:** `/opt/rayuela/ferias/venv` (ferias, demo, prueba), `/opt/rayuela/novedades/venv`,
   `/opt/rayuela/tapas_externas/venv` (Pillow).
4. **Código:** clonar `rayuela-demo` y `rayuela-docs`; ferias y novedades desde su repo.
5. **Configuración:** copiar `units/*` a `/etc/systemd/system/`, `nginx/*` a
   `/etc/nginx/sites-available/` con symlinks en `sites-enabled`, `bin/*` a `/usr/local/bin/`.
6. **Secretos:** recrear `/etc/rayuela/*.env` desde el gestor de contraseñas (ver `SECRETOS.md`).
7. **Datos:** restaurar `catalogo-*.db.gz` en `/opt/rayuela/demo/catalogo.db`; opcionalmente fichas
   y tapas (hoy sin respaldo: se regeneran desde Bridge o desde scraping).
8. **TLS:** `certbot --nginx -d demo.rayuelalaplata.com.ar -d ferias...` (los 5 subdominios).
9. **Verificar:** `bash /opt/rayuela/demo/publicar.sh` (humo de la demo),
   `python3 /opt/rayuela/ferias/humo.py`, `python3 /opt/rayuela/novedades/humo.py`.
