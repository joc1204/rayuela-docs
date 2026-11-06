# Pendientes del proyecto Rayuela

**Actualizado:** 04/11/2026 17:50
**Regla:** cada vez que se cierra un pendiente, se marca acá el mismo día. Lo que no está acá no existe.

Estados: ✅ hecho · 🔄 en curso · ⬜ pendiente · ⛔ bloqueado (espera a alguien)

---

## 1 · Diseño de la tienda demo

| # | Pendiente | Estado | Nota |
|---|---|---|---|
| D1 | Filtros y orden en la búsqueda | ✅ | editorial, temas, stock, 5 órdenes, chips |
| D2 | Índice de texto para buscar rápido | ✅ | FTS5; reindexar cuando vuelva la sincronización |
| D3 | Recomendados al pie como carrusel | ✅ | 12 tarjetas, excluye el mismo libro |
| D4 | **Esqueletos de carga** (búsqueda y tapas) | ✅ | esqueleto al tipear y fundido de tapas |
| D5 | **Estados vacíos con salida** (búsqueda, lista, carrito) | ✅ | con CTA a WhatsApp y subir lista |
| D6 | **Página institucional** dentro de la demo | ✅ | `/nosotros`, con sucursales y cómo comprar |
| D7 | Revisión completa en celular de cada pantalla | ⬜ | tablas ya desplazables; falta que la miren en un teléfono real |
| D8 | Ficha: bloque de retiro y horarios | ⛔ | faltan los horarios (Verónica) |
| D9 | Carteles: probar impresión A7 y doble faz | ⬜ | imprime en el local |
| D10 | Aviso en el admin de la fecha de los datos | ✅ | muestra "datos al 04/11/2026 10:25 · actualización pausada" |
| D11 | Carrito: demostración sin cierre de compra | ✅ | carga, suma, quita y total; sin WhatsApp y sin pago |
| D12 | Lista: opción de foto | ⬜ | retirada hasta probarla con listas reales |
| D14 | Búsqueda tolerante a errores de tipeo | ✅ | "¿Quisiste decir?": 'borgs'→borges (395), 'alehp'→aleph (10), 'pachora'→pachorra (3) |
| D13 | Apex `rayuelalaplata.com.ar` (redirección o página) | ⛔ | decisión de Jorge + DNS en Cloudflare |

## 2 · Datos y contenido

| # | Pendiente | Estado | Nota |
|---|---|---|---|
| C1 | Editorial completada desde las fichas locales | ✅ | 41.455 títulos |
| C2 | Medir motores de scraping con el código real del proyecto | ⬜ | zivals / yenny / sbs; mi prueba previa no vale |
| C3 | Definir orden de fuentes del scraping | ⬜ | depende de C2 |
| C4 | Completar sinopsis, páginas y rubros de los que no tienen ficha | ⛔ | depende de C2/C3 y del OK de Jorge |
| C5 | Campos nuevos con trazabilidad (`editorial_web`, `sinopsis_web`, `rubros_web`, `web_revisado`) | ⬜ | no pisan lo de Bridge |
| C6 | Pantalla "datos de la web para revisar" (para Verónica) | ⬜ | después de C5 |
| C7 | Normalizar nombres de editorial ("HOMO SAPIENS" vs "Homo Sapiens Ediciones") | ⬜ | necesario para comparar por editorial |

## 3 · Infraestructura y Bridge

| # | Pendiente | Estado | Nota |
|---|---|---|---|
| B1 | Todos los trabajos de Bridge apagados y fuera de systemd | ✅ | 12 unidades en `/etc/rayuela/unidades-off/` |
| B2 | Limitador global 3 pedidos/s + candado entre trabajos | ✅ | probado con dos procesos en paralelo |
| B3 | Reanudar trabajos | ⛔ | Bloqueado: Bridge exige token; el token recibido da 401. Vero trata con Luis (04/11 22:00) |
| B8 | Obtener token de Bridge y forma de enviarlo | ⛔ | pedido a Luis; ver §15.19 del técnico |
| B4 | Reindexar la búsqueda al reanudar la sincronización | ⬜ | correr `indexar_busqueda.py` (3 s) y `indexar_palabras.py` (4 s) |
| B5 | Escribir informe con la cronología para soporte de Bridge | ✅ | `Informe-técnico-carga-Bridge.docx` |
| B6 | Revisar si conviene otro horario/frecuencia de sync | ⛔ | después del incidente y de hablar con Luis |
| B7 | Copia de respaldo de la base antes de cada tanda grande | ⬜ | hay respaldo diario 03:10 |

## 4 · Negocio y decisiones de Verónica

| # | Pendiente | Estado | Nota |
|---|---|---|---|
| V1 | Horario de atención y medios de pago | ⛔ | los tiene que dar el local |
| V2 | Fichas incompletas (editorial, temas) | ⛔ | las completa el personal |
| V3 | Portada del libro en el panel de Bridge | ⛔ | pedido a Luis |
| V4 | Reservas y ventas por API | ⛔ | Luis; probar en vivo antes de prometer |
| V5 | Formato del QR de consulta y carteles | ⬜ | ver si le sirven al personal |
| V6 | Decidir si el bloque rojo del logo va en la cabecera | ⛔ | lo evalúa Verónica |
| V7 | Alertas de Telegram del equipo (grupo, varios destinatarios, horarios silenciosos) | ⬜ | hoy avisa a un solo chat |

## 5 · Técnico y operación

| # | Pendiente | Estado | Nota |
|---|---|---|---|
| T1 | Documento de control del proyecto | ✅ | `estado/PROYECTO-ESTADO.md` |
| T2 | Protocolo de riesgo por solicitud (6 ejes) | ✅ | en el documento de control |
| T3 | Modo calle (Telegram cada N minutos) | ⛔ | apagado hasta que Jorge lo pida |
| T8 | **Puerta de publicación** (`publicar.sh` + `humo.py`) | ✅ | 05/11: humo 8/8; rechazo y rollback probados |
| T9 | **Verificación de hechos** (`verificar_hechos.py`) | ✅ | 05/11, sin tocar Bridge |
| T10 | **Registro de proyectos** (`PROYECTOS.md`) | ✅ | 05/11 |
| T11 | **Inventario de UI** (`INVENTARIO-UI.md` + humo) | ✅ | 05/11 |
| T12 | Unificar el scraper duplicado (Novedades ↔ tapas externas) | ⬜ | cambio cruzado: probar los dos consumidores |
| T13 | Limpiar dato basura: código `0000000000000` existe como producto | ⬜ | decidir con Rayuela |
| T14 | Probar la puerta de humo con un cambio que rompa a propósito | ✅ | 05/11: rechazó 2 publicaciones y restauró sola |
| T15 | Infraestructura versionada (`infra/`: units, nginx, bin, env de ejemplo) | ✅ | 05/11 |
| T16 | Inventario de secretos (`SECRETOS.md`) | ✅ | 05/11, sin valores |
| T17 | Cargar las 2 claves de deploy en GitHub (ferias y novedades) | ✅ | 05/11, cargadas por Jorge |
| T18 | Subir commits de ferias y novedades a GitHub | ✅ | 05/11: ferias `4da5122` · novedades `0d1cd6f` |
| T19 | Comparar código desplegado en el VPS vs repos | ⬜ | ferias y novedades no tienen git en el servidor |
| L1 | Limpieza automatica fase 1 (precio < 15.000 y sin stock) | ↩️ revertida | 05/11 22:30: se pasó a control manual exclusivo |
| L2 | Limpieza automatica fase 2 (precio irrisorio) | ↩️ revertida | 05/11 22:30 · el CSV de precios sigue siendo útil |
| L6 | **Panel de limpieza por criterios** (`/admin/limpieza`) | ✅ | 05/11: filtro por precio/stock, ocultar y volver a mostrar, por selección o por lote entero |
| L7 | Modo de limpieza: **manual** (decidido por Jorge el 05/11) | ✅ | la librería ya usa la demo; control absoluto de quien administra |
| L8 | Guía corta para quien administra la limpieza | ✅ | `Guia-para-administrar-la-limpieza.docx` |
| L9 | Modo automático por stock mínimo | ❌ descartado | se evaluó y se prefirió manual |
| L10 | Panel de limpieza: filtro por editorial y exportación a CSV | ✅ | 05/11 |
| L12 | Los ocultos sobreviven a la sincronización (trigger + control en la puerta) | ✅ | 05/11: probado actualización, recreación de fila y oculto manual |
| L11 | Recordar a la librería que las correcciones se hacen en Bridge | ⬜ | el panel sólo oculta en la vitrina; Bridge es la fuente de la verdad |
| L13 | Reglas automaticas de limpieza | ❌ descartadas | la coherencia manda: solo filtra el admin desde el panel |
| L3 | Que Vero defina piso definitivo y criterio de no-libros | ⬜ | resumen `Limpieza-del-catalogo-para-Vero.docx` |
| L4 | Corregir los 874 precios del CSV y volver a mostrarlos | ⬜ | requiere precios reales (Bridge o carga manual) |
| L5 | Tandas nocturnas de enriquecimiento externo (20 mil con stock) | 🔄 | 1.398 completados de 2.000 el 05/11 |
| H1 | **`appctl` en la netbook**: apagar/encender un proyecto sin afectar los demás | ⬜ | comando + marca de apagado intencional + despublicar del túnel + bot de Telegram |
| H2 | Verificar el estado de la netbook (4 datos) | ⬜ | qué corre, cómo publica el túnel, qué hace `funnel-check`, Node-RED bajo pm2 |
| H3 | Repo `host-netbook` (units, manifiestos, humo-host, publicar-host) | ⬜ | propuesta escrita en `HOST-NETBOOK.md` |
| A1 | Activar el trabajo con agentes especializados | ⬜ | el método y las puertas están listos; los agentes se crean por demanda |
| B1 | **Respaldo externo** (cifrado) | ✅ | 05/11: paquete de 58 MB en Drive (cuenta de desarrollo) y en la PC |
| B1b | Automatizar el respaldo externo a Drive (rclone + timer) | ✅ | 05/11: diario 03:40, 3 generaciones en Drive |
| B1c | Rotar la passphrase y guardarla en el gestor | ⬜ | la actual se mostró una vez en el chat |
| B2 | Secretos al gestor de contraseñas | ⬜ | lo hace Jorge; la lista está en `SECRETOS.md` y la passphrase del respaldo va ahí |
| B3 | Probar una restauración completa | ⬜ | después de B1 |
| T4 | Leer audios de Telegram | ⬜ | hoy se guardan, no se transcriben (habría que instalar Whisper) |
| T5 | Revisar que las consultas se avisen bien (verificación HTTP) | ✅ | ahora verifica y reintenta |
| T6 | Limpiar consultas de prueba del panel | ⬜ | 3 registros de Jorge |
| T7 | Revisar accesos y claves del VPS | ⬜ | cuando Jorge lo disponga |
