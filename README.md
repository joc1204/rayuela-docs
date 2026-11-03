# Rayuela · Documentación y configuración

Todo lo que hay que saber y tener para operar, mantener y **entregar** la
infraestructura digital de la librería Rayuela.

> **Repositorio privado.** No contiene contraseñas ni claves: los secretos viven
> en el servidor (ver `tecnico/TECNICO-TRASPASO.md`, sección "Credenciales").

**Última actualización:** 03/11/2026

---

## Por dónde empezar

| Si sos… | Empezá por |
|---|---|
| La persona que toma el control | `tecnico/TECNICO-TRASPASO.md` (todo el mapa + runbook + checklist de traspaso) |
| Alguien que va a operar el día a día | `operacion/procedimiento-operativo.md` (deploy, verificación, rollback) |
| Quien decide qué se construye | `plan/RAYUELA-BACKLOG.md` (módulos aprobados, decisiones y costos) |
| Quien usa la app | `manuales/Manual-Rayuela-Ferias.pdf` |

## Contenido

```
tecnico/     TECNICO-TRASPASO.md      documento maestro: infraestructura, cuentas,
                                      runbook, seguridad, respaldos, riesgos, traspaso
plan/        RAYUELA-BACKLOG.md       módulos aprobados y pendientes, con decisiones
reglas/      RAYUELA-REGLAS.md        reglas de trabajo con Jorge
servidor/    SERVIDOR-DESPLIEGUE-Y-TUNEL.md   netbook, túnel de Tailscale y servicios
             config/                  copia fiel de lo que corre en el servidor
               nginx/                 sitios y límites
               systemd/               unidades y timers
               ssh/                   endurecimiento de SSH
               scripts/               respaldo, salud y refresco del ambiente de prueba
manuales/    Manual-Rayuela-Ferias (docx/pdf) y Guía de Novedades (docx/pdf)
             generadores/             scripts que los regeneran
qr/          QR definitivos (PNG y hojas A4 para imprimir)
             generadores/             scripts que los regeneran
operacion/   procedimiento-operativo.md · verificar_netbook.sh
```

## Ambientes

| Ambiente | URL | Qué es |
|---|---|---|
| Producción | `https://ferias.rayuelalaplata.com.ar` | App real de ferias |
| Lector cliente | `https://lector.rayuelalaplata.com.ar` | Consulta de precios (público) |
| Lector vendedor | `https://lector.rayuelalaplata.com.ar/?m=v` | Con ficha completa |
| Prueba | `https://prueba.rayuelalaplata.com.ar` | Copia aislada, datos descartables |
| Novedades | `https://net-casa.tailfb7a36.ts.net/novedades` | Bot de novedades (netbook del local) |

**Regla:** nada se instala en producción sin pasar por `prueba.`.

## Cómo actualizar esta documentación

### Copia de las configuraciones del servidor (`servidor/config/`)

Cuando cambie algo de nginx, systemd o ssh en el servidor, volver a bajarlas:

```bash
# en el servidor
cd / && tar czf /root/rayuela-config.tar.gz \
  etc/nginx/sites-available/{ferias,rayuela-apps,prueba} \
  etc/nginx/conf.d/99-rayuela.conf etc/nginx/proxy_rayuela.conf \
  etc/systemd/system/{ferias,ferias-prueba}.service \
  etc/systemd/system/rayuela-{respaldo,salud}.{service,timer} \
  etc/ssh/sshd_config.d/60-rayuela.conf \
  usr/local/bin/rayuela-{salud,respaldo}.sh root/refrescar-prueba.sh
```

Bajar el `.tar.gz`, extraer sobre `servidor/config/` y **volver a redactar**
`FERIAS_SECRETO` en `systemd/ferias.service`.

### Manuales

```bash
python manual/construir_manual.py           # Word + PDF
python manual_novedades/construir_guia.py   # Word + PDF
```
Después copiar los archivos nuevos a `manuales/`.

### QR

```bash
python qr/generar_qr_final.py    # PNG y hojas A4
```
Los PDF se generan con el mismo script (o exportando la hoja A4 a 300 dpi).

## Lo que NO va acá (nunca)

- Contraseñas, claves de API, tokens, claves SSH
- Bases de datos (`*.db`), respaldos
- La clave de sesión `FERIAS_SECRETO`

Si alguna vez hace falta pasarlos, va por gestor de contraseñas, nunca por el repo.
