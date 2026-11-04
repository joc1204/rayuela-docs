# Pendientes del proyecto Rayuela

**Actualizado:** 04/11/2026 15:25
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
| D7 | Revisión completa en celular de cada pantalla | ⬜ | la va a mirar Verónica desde el teléfono |
| D8 | Ficha: bloque de retiro y horarios | ⛔ | faltan los horarios (Verónica) |
| D9 | Carteles: probar impresión A7 y doble faz | ⬜ | imprime en el local |
| D10 | Aviso en el admin de la fecha de los datos | ⬜ | "catálogo al 04/11 10:25" |
| D11 | Apex `rayuelalaplata.com.ar` (redirección o página) | ⛔ | decisión de Jorge + DNS en Cloudflare |

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
| B3 | Reanudar trabajos (sábado 7/11 desde la 1:00, de a uno) | ⛔ | espera OK de Jorge y de Rayuela |
| B4 | Reindexar la búsqueda al reanudar la sincronización | ⬜ | 3 segundos, sin Bridge |
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
| T4 | Leer audios de Telegram | ⬜ | hoy se guardan, no se transcriben (habría que instalar Whisper) |
| T5 | Revisar que las consultas se avisen bien (verificación HTTP) | ✅ | ahora verifica y reintenta |
| T6 | Limpiar consultas de prueba del panel | ⬜ | 3 registros de Jorge |
| T7 | Revisar accesos y claves del VPS | ⬜ | cuando Jorge lo disponga |
