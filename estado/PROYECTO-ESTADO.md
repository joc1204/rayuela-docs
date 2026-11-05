# Estado del proyecto Rayuela — documento de control

**Última actualización:** 04/11/2026 15:00 (hora Argentina)
**Para qué sirve:** que quien trabaje en el proyecto (yo, en cada turno) lea esto **antes** de proponer o
ejecutar nada, y no invente algo que ya está resuelto ni repita un error ya cometido.

> Regla madre: **propongo, Jorge autoriza, después ejecuto.** Nada en producción sin OK explícito.

---

## 1 · Protocolo de evaluación de riesgo (obligatorio en cada solicitud)

Antes de proponer o ejecutar cualquier cosa, se evalúa y se informa el riesgo **en los seis ejes**.
Una propuesta que no trae esta evaluación está incompleta.

### 1.1 Los seis ejes

| Eje | Pregunta que hay que contestar | Escala |
|---|---|---|
| **Tiempo** | ¿Cuánto tarda? ¿bloquea otras tareas? | < 5 min · < 1 h · horas · días |
| **Tokens** | ¿Cuántos turnos y cuánto contexto consume? ¿Hay un camino más barato? | bajo · medio · alto |
| **Infraestructura Rayuela** | ¿Consulta Bridge? ¿Cuántos pedidos? ¿En qué horario? ¿Se puede evitar? | 0 · puntual · lote nocturno · **masivo (prohibido sin OK)** |
| **Infraestructura VPS** | ¿CPU/RAM? ¿Reinicia servicios? ¿Afecta la demo que puede estar mirando Verónica? | bajo · medio · alto |
| **Terceros** | ¿Scraping a librerías? ¿Qué ritmo? ¿Respeta sus términos? | lectura puntual · lote · masivo |
| **Reputación** | ¿Lo ve Rayuela o Verónica? ¿Puede parecer que rompimos algo? ¿Queda expuesto un error nuestro? | bajo · medio · alto |

Y siempre se responden dos más:

- **Eficacia**: ¿resuelve el pedido completo o sólo una parte?
- **Eficiencia**: ¿hay un camino más corto, más barato o más seguro? Si lo hay, se dice aunque no lo hayan pedido.

### 1.2 Reglas de decisión

1. **Riesgo de infraestructura Rayuela distinto de cero** → se propone con estimación de pedidos y horario, y **se espera OK**. Nunca "pruebo y veo".
2. **Cualquier consulta a Bridge fuera de la ventana 21-8** (excepto el endpoint de ferias que dispara una persona) → prohibido sin indicación expresa.
3. **Riesgo de reputación medio o alto** → se avisa explícitamente antes de actuar, aunque el riesgo técnico sea bajo.
4. **Si hay riesgo de que la demo muestre algo mal** (datos viejos, un error visible, un texto equivocado) → se dice antes, no después.
5. **Toda acción riesgosa se propone junto con**: qué exactamente se va a hacer, cómo se verifica, y **cómo se revierte**.
6. **Ninguna acción se clasifica a sí misma como "inocua"**. Si toca un servicio externo o dice algo sobre la infraestructura, pasa por el protocolo.

### 1.3 Formato de propuesta

```
PROPUESTA: <qué>
Riesgo: tiempo <x> · tokens <x> · Rayuela <x> · VPS <x> · terceros <x> · reputación <x>
Eficacia: <completa / parcial>
Alternativa más eficiente: <sí/no, cuál>
Verificación: <cómo compruebo que salió bien>
Reversión: <cómo se deshace>
```

---

## 2 · Reglas de verificación (para no volver a inventar)

1. **Fuente de verdad primero**: antes de afirmar algo sobre los sistemas de Jorge, buscar en el
   workspace si ya existe el código, la documentación o el dato (`grep` sobre el proyecto). Leerlo y usarlo.
2. **Si mi prueba contradice su código, gana su código** hasta demostrar lo contrario con evidencia.
3. **Toda afirmación de estado va con evidencia**: archivo y línea, o comando y salida.
4. **Leer las notas antes de actuar**, no sólo para redactar documentos.
5. **No repetir decisiones ya tomadas**: si está acá, está decidido; no se vuelve a preguntar.

### Errores cometidos (para no repetirlos)

| Fecha | Error | Causa | Regla que lo previene |
|---|---|---|---|
| 03/11 19:00 | 37 pedidos/s a Bridge durante el cierre de caja (9 hilos de tapas + stock + fichas) | Subir paralelismo sin calcular la carga total, en horario comercial | Eje infraestructura + ventana 21-8 + limitador 3/s + candado |
| 04/11 | Consultas de clientes avisadas "enviadas" sin verificar la respuesta de Telegram | Marcar estado sin comprobar el resultado real | Verificar antes de declarar hecho |
| 04/11 | URL inventadas de zivals/yenny/sbs → conclusión falsa "esas librerías no funcionan" | No leer `rayuela_scrapping/novedades/sitios.py`, que ya existía en el proyecto | Fuente de verdad primero |
| 04/11 | Muestra de 20 ISBNs sesgada (todos de Oxford) | Elegir la muestra sin mirar qué contenía | Mirar la muestra antes de concluir |

---

## 3 · Inventario: qué existe ya (no inventar de nuevo)

### Scraping de librerías — proyecto `rayuela_scrapping`
- Paquete `novedades`, módulo `sitios.py` con **tres motores**: `zivals`, `yenny`, `sbs`.
- URLs reales: `zivals.com.ar/LIBRO/<isbn>` · `yenny-elateneo.com/search/?q=<isbn>` (luego detalle) ·
  `sbs.com.ar/<isbn>`.
- Campos que ya extrae: editorial, autor, sinopsis, tema/rubros, páginas, encuadernación, idioma,
  año, precio, tapa.
- Medición del 04/11 con las URLs correctas: zivals 12/12, yenny 12/12, buscalibre 12/12.
  **SBS no se midió bien con mi prueba genérica** (usa JSON de VTEX, el motor del proyecto lo sabe leer).
- Este scraper es el mismo que alimenta Novedades y el que se usó para tapas externas.

### Tienda demo (`demo_tienda`, `demo.rayuelalaplata.com.ar`)
- Flask + SQLite (`catalogo.db`): 447.607 títulos, 428.674 publicables, 26.439 con stock.
- Portada con personalización (Fase 0, 1 y 2): "Seguí mirando", "Lo más visto", "Según lo que miraste",
  "También te puede interesar" (carrusel, excluye el mismo libro por título+editorial+precio, mínimo 3).
- Subir lista con PDF/foto (OCR) en dos pasos, con revisión y edición línea por línea.
- Carteles con QR al panel de consulta, panel de consultas avisadas por Telegram.
- Identidad visual: logo oficial, favicon (R blanca sobre rojo), tarjeta para compartir.
- Editorial completada desde fichas locales: **41.455 títulos** (antes 1).

### Apps y servicios en el VPS (201.32.132.197)
- `rayuela-demo` (:5052) tienda demo · `ferias` (:5050) app de ferias · `ferias-prueba` (:5051) ·
  `rayuela-novedades` (:5060) · nginx, certbot, fail2ban, respaldo diario 03:10.
- Bot Telegram `@RayuelaRepoBot_bot`; helpers `avisar`, `preguntar`, `leer-respuestas`, `leer-telegram`
  (este último lee texto, audios y archivos y guarda la cola en `/var/lib/rayuela-telegram/`).

---

## 4 · Qué está apagado y por qué (no reactivar sin OK)

| Qué | Estado | Motivo |
|---|---|---|
| Todos los trabajos de Bridge (sync rápida, stock, metadatos, fichas, tapas) | **fuera de systemd** (`/etc/rayuela/unidades-off/`), bandera `/etc/rayuela/pausa-bridge` | incidente del 03/11 |
| Consulta de fichas desde la web demo | bloqueada por `/opt/rayuela/demo/PAUSA_BRIDGE` | idem |
| Sincronización automática de precios de la app de ferias | `precios_activo = 0` | no debe actualizar antes de que haya una feria abierta |
| Modo calle (chequeo de Telegram cada N minutos) | apagado | consume tokens sin valor en cada vuelta |
| `rayuelalaplata.com.ar` (apex) | sin registro, a propósito | reservado para el portal futuro |
| Tapas externas | detenido | no toca Bridge, pero se apagó todo por precaución |

**Reanudación:** sábado 7/11 desde la 1:00, de a un trabajo por vez, dentro de la ventana 21-8.
Nada el viernes 6/11 (evento en Rayuela hasta las 23:30/24:00).

---


### 4.1 · Doble llave: nada sale hacia Rayuela sin autorización de Jorge (04/11, 19:20)

Todo script que consulta Bridge verifica **dos archivos** antes de arrancar:

1. Debe existir `/etc/rayuela/autorizacion-bridge` (permiso explícito de Jorge, se crea sólo cuando
   él lo indica y dice hasta cuándo vale).
2. No debe existir `/etc/rayuela/pausa-bridge` (corte inmediato).

Si falta la autorización, el script sale con:
`SIN AUTORIZACION: falta /etc/rayuela/autorizacion-bridge. No se consulta Bridge sin indicacion de Jorge.`

Además: `sincronizar.traer()` (la función por la que salen todos los pedidos) vuelve a chequear lo
mismo, así que aunque alguien reutilice el código por otro camino, se niega. Y la web de la demo
tampoco pide fichas sin autorización.

Para habilitar algo: Jorge pide, se crea el archivo con la fecha, se corre **un solo** trabajo, y se
borra. Para cortar todo: se borra el archivo.


### 4.2 · Decisión del 04/11, 22:00: se deja todo detenido

Jorge comunica la situación a Verónica y **ella trata con Luis** (Bridge). Hasta que haya respuesta:

- Todos los trabajos de actualización **detenidos** (0 procesos, 0 conexiones establecidas).
- `pausa-bridge` presente y **sin autorización**.
- `PAUSA_BRIDGE` en la web: la demo no pide fichas.
- Unidades de carga fuera de systemd.

**Motivo**: Bridge activó el requerimiento de token (entre las 18:23 y las 21:26 del 04/11) sin avisar a la
librería, y el token que tiene Jorge devuelve **401 "Token inválido"**. Sin credencial válida no se
puede actualizar stock, fichas ni tapas.

**Cuando Bridge entregue el token válido y la URL exacta de la v1** (o confirme que la v0 sigue),
el trabajo pendiente es de minutos: cargar el token en `/etc/rayuela/bridge.env`, crear la
autorización, correr un pase acotado y verificar.

## 5 · Decisiones tomadas (no volver a preguntar)

| Fecha | Decisión |
|---|---|
| — | Bridge: **sólo lectura**, nunca escritura; reservas sin probar hasta validar en vivo con el personal |
| — | Un libro tiene **un único precio** (el de tapa). Los adicionales son por envío/despacho/forma de pago y van aparte |
| 04/11 | La tienda demo vive en `demo.rayuelalaplata.com.ar`; el apex queda para después |
| 04/11 | Ventana de trabajo nocturna **21 a 8**; nada de Bridge fuera de eso |
| 04/11 | **Sin actualización automática de precios** mientras no haya una feria abierta |
| 04/11 | **Viernes 6/11 bloqueado**; reanudar sábado 7/11 a la 1:00 |
| 04/11 | Publicación: todos los títulos con datos esenciales, con o sin stock ("a pedido") |
| 04/11 | Datos personales: sesión anónima, cookies propias, purga a 90 días, aviso en el pie |
| 04/11 | Respuestas por **ambos canales** cuando el modo calle está activo (chat + Telegram) |
| 04/11 | La bajada dice **"desde 1991"** (lo confirma el logo oficial) |

---

## 6 · Pendientes conocidos

| Pendiente | Depende de |
|---|---|
| Completar editorial/sinopsis/páginas de los que no tienen ficha | scraping con `rayuela_scrapping` (no toca Bridge) |
| Definir cuál motor de scraping va primero | medición con el scraper real del proyecto |
| Horario y medios de pago del local | Verónica |
| Reindexar la busqueda (`indexar_busqueda.py`) al reanudar sincronizaciones | 3 segundos, sin Bridge |
| Fichas incompletas (editorial, temas) | personal de Rayuela |
| Portada del libro en el panel de Bridge | pedido a Luis |
| Reservas y ventas por API | Luis |
| Apex online (redirección o página institucional) | decisión de Jorge + DNS en Cloudflare |

---

## 7 · Cómo se comprueba que Bridge está en cero

```bash
ss -tan | grep -c ':9090'                 # debe dar 0
systemctl is-active rayuela-demo-rapido   # not-found
ls /etc/rayuela/pausa-bridge             # debe existir
```

Si alguna de las tres falla, **no se declara "cortado"** hasta resolverla.

## Decisiones del 05/11/2026: limpieza del catálogo

| Tema | Decisión |
|---|---|
| Filtro de precio | ocultar los menores a $15.000 **sin stock**; los que tienen stock se respetan (salvo precio irrisorio) |
| Precio irrisorio | los que tienen stock con precio menor a $1.000 se ocultan como error de carga (874) |
| Stock | se filtra **por cantidad** (desde/hasta) porque el conteo no es fiel; se usa como margen de seguridad |
| Modo | **manual**: la librería decide qué ocultar desde el panel, no el sistema |
| Por qué manual | la demo ya está en uso por la librería y prefieren control absoluto para evaluar |
| Reversibilidad | todo se marca (`filtro = 1`), nunca se borra; se puede revertir por lote o desde el panel |

### Fuente de la verdad (05/11/2026)

Las correcciones de datos (precios, stock, altas y bajas) **se hacen en Bridge**. El panel de la demo
sólo decide qué se muestra en la vitrina: ocultar un título ahí no corrige el sistema ni reemplaza el
trabajo en Bridge. El panel lo dice en pantalla, para que nadie confunda las dos cosas.
