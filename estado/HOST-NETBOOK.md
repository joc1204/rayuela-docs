# Host de la netbook: arranque y túnel compartidos

**Estado:** propuesta para implementar en la netbook (`domotica-bangho`, 192.168.1.19).
**Motivo:** Node-RED, Presupuestito y Gastos comparten máquina, arranque y túnel. Hoy esa capa vive
en un documento de prosa (`SERVIDOR-DESPLIEGUE-Y-TUNEL.md`); no es fuente de verdad ni se verifica.

## Por qué el documento actual no alcanza

- **Es prosa**: no impide que alguien edite un `.service` y rompa otro proyecto.
- **No verifica**: no hay ninguna prueba que diga "las cuatro apps y el túnel están arriba".
- **No tiene vuelta atrás**: si un cambio de arranque deja un servicio caído, se descubre por el reclamo.
- **No separa responsabilidades**: un mismo lugar dice todo, y al editarlo se toca lo de todos.

## Estructura propuesta: un repositorio `host-netbook`

```
host-netbook/
├── inventario.md          # puertos, apps, rutas, unidades, URLs públicas, dueño
├── units/                 # fuente de verdad de systemd (symlinks a /etc/systemd/system)
│   ├── gastos.service
│   ├── presupuestito.service
│   ├── ferias.service
│   ├── rayuela-novedades.service
│   ├── tunel.service
│   └── tunel-check.timer  +  tunel-check.service
├── manifiestos/
│   ├── gastos.yaml        # ruta, puerto, URL de salud, comando de deploy, rollback
│   ├── presupuestito.yaml
│   ├── ferias.yaml
│   └── novedades.yaml
├── deploy/<app>.sh        # despliegue por app: nunca toca otra
├── humo-host.py           # verifica TODAS las apps + el túnel + puertos
└── publicar-host.sh       # puerta: verifica unidades, reinicia sólo lo cambiado, corre humo
```

### Reglas que resuelven el problema

1. **Una unidad por app. Nunca una unidad "que arranca todo".** Cambiar el arranque de Gastos sólo
   reinicia `gastos.service`.
2. **El túnel es una unidad aparte**, con `Restart=always`, y su propio chequeo
   (`tunel-check.timer` cada 5 minutos: si no responde, lo reinicia y avisa por Telegram).
3. **`After=network-online.target` + `Wants=network-online.target`** en todas: arrancan después de
   la red, no en competencia.
4. **Registro de puertos** en `inventario.md`. Publicar una app con un puerto ya usado es error de
   la puerta, no sorpresa en producción.
5. **Nadie edita unidades de otro proyecto**: cada manifest declara su dueño; la puerta rechaza el
   cambio si el archivo pertenece a otra app.
6. **Límites por unidad** (`MemoryMax`, `Restart=on-failure`, `RestartSec`) para que una app no deje
   sin memoria a las demás.

### `publicar-host.sh` (la puerta)

```
1. systemd-analyze verify units/*.service        → sintaxis y dependencias
2. diff contra el estado actual                  → qué unidad cambió
3. daemon-reload + restart SÓLO de esa unidad
4. humo-host.py                                  → todas las apps y el túnel siguen arriba
5. si algo falla: restaura la unidad anterior y reinicia
```

### `humo-host.py` (lo que verifica)

- Cada unidad del inventario está `active`.
- Cada puerto declarado está escuchando.
- Cada URL de salud responde 200 (local).
- El túnel responde desde afuera (una URL pública).
- Ninguna unidad quedó en estado `failed`.
- Orden de arranque: las apps no dependen del túnel para servir localmente.

## Cómo se migra (5 pasos, sin tocar los proyectos)

1. Copiar las unidades actuales a `units/` y symlinkear (systemd sigue usando los mismos archivos).
2. Escribir `inventario.md` con puertos y salud reales (verificados, no de memoria).
3. Escribir `manifiestos/*.yaml` y `humo-host.py`; correrlo para tener la línea de base.
4. Crear la unidad del túnel y el chequeo periódico.
5. Instalar `publicar-host.sh` y usar **sólo** ese camino para cambios de arranque.

## Lo que esto no resuelve

- No reemplaza la documentación de cada app: cada proyecto sigue con su propio README.
- No automatiza el despliegue de código: eso lo hace cada `publicar.sh` de su proyecto.

## Relación con Rayuela

La netbook y el VPS son máquinas distintas. El VPS ya tiene su propia puerta (`publicar.sh` por
proyecto) y su política de carga (`POLITICA-CARGA-BRIDGE.md`). La netbook sólo aloja
Node-RED, Presupuestito y Gastos: **nada de Rayuela corre ahí**.
