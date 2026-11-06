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
| L14 | Pantalla única del catálogo (`/admin/catalogo`) | ✅ | 05/11: unifica "qué se publica" y "limpiar por criterios"; busca por texto/ISBN, oculta, muestra y destaca |
| L15 | Auditoria de interfaz obligatoria en la puerta (`auditar_ui.py`) | ✅ | 05/11: humo + auditoria + restauracion automatica |
| L16 | Revision independiente de UI antes de publicar | ✅ | 05/11: informe en `_revision/` |
| L17 | Revision independiente de UI: 2 criticos detectados | ✅ | 05/11: informe en `revision/2026-11-05-admin-ux.md` |
| L18 | Critico: "Traer cambios ahora" no sincronizaba (formulario anidado) | ✅ | corregido con `formaction`; el auditor ahora detecta formularios anidados |
| L19 | Critico: "oculto" nombraba dos estados distintos | ✅ | estado de la tienda cuenta `filtro`; un solo rotulo en pantalla y CSV |
| L20 | Importantes del informe (numeros, criterio "Ver: ocultos", textos, pausa, consultas) | ✅ | 9 de 9 corregidos |
| L21 | Menores del informe (nombres de portada, Carteles duplicado, ejemplos) | ✅ | corregidos en la misma tanda |
| L22 | Segunda revision independiente: 1 critico (WhatsApp) + 14 hallazgos | OK | 05/11: informe en revision/2026-11-05-admin-ux-2.md |
| L23 | Auditor verifica WhatsApp, paginacion, tablas con estilo y pantallas con filtro | OK | tambien detecta formularios anidados |
| L24 | Pendiente de la revision: cabecera/pie de tienda en el panel y menu de seccion | pendiente | jerarquia, no error |
| L25 | Prueba en telefono real (CSS ya no oculta columnas) | pendiente | se junta con D7 |
| L26 | Regla global de stock eliminada del panel (duplicaba el filtro del catalogo) | OK | 05/11: ajuste, codigo y textos fuera; auditor la prohibe |
| L27 | Catalogo unificado en una pantalla con pestanas (Listado, Calidad, Estado) | OK | 05/11: publicada; calidad.html y estado.html absorbidas |
| L28 | Revision independiente previa a publicar: NO publicar (doble h1, mensaje duplicado, falsos positivos del auditor) | OK | informe en revision/2026-11-05-catalogo-pestanas.md; todo corregido antes de publicar |
| L29 | Copia de prueba en otro puerto para validar el gate antes de produccion | OK | /tmp/staging-demo en 5053: humo 11/11 y auditoria 0 antes de publicar |
| L30 | Auditar contenido de las pestanas (no solo 200) | OK | humo valida titulo unico y contenido de cada pestana |
| L31 | Pendiente: menu de seccion y cabecera/pie de tienda en el panel | pendiente | jerarquia, no error |
| L32 | Pendiente: prueba en telefono real | pendiente | se junta con D7 |
| L33 | Fuera el cartel de DEMO del panel y de la tienda | OK | 05/11: seccion "Precios"; el aviso del carrito explica sin decir demo |
| L34 | La tienda no debe presentarse como demo al publico | OK | el auditor prohibe "cartel de DEMO" y "banner_demo" |
| L35 | Fuera la opcion de ocultar precios: una tienda siempre muestra precios | OK | 05/11: ajuste, codigo y seccion del panel eliminados; auditor lo prohibe |
| L36 | publicar.sh avisa cuando no hay archivos nuevos (publicacion vacia) | OK | 05/11: huella de app.py, templates y css |
| L37 | publicar.sh verifica que los archivos esten en el servidor antes de publicar | pendiente | hoy se detecta por el aviso de la firma |
| L38 | Escrituras del scraping en tandas: el panel ya no espera al bloqueo de la base | OK | 05/11: de hasta 30 s a menos de 0,01 s |
| L39 | Busqueda por argumento: indice con sinopsis y ranking ponderado | OK | 06/11: 428.674 filas, titulo x10, autor x6, temas x3, sinopsis x1 |
| L40 | Busqueda tolerante a recuerdos vagos: stopwords + OR + aviso "ampliamos" | OK | 06/11: de 0 resultados a 8 en frases como "chicos jugando a la pelota" |
| L41 | Cobertura de argumento limitada por fichas faltantes | pendiente | 36.273 publicables con sinopsis; crece con el enriquecimiento |
| L42 | Bloque aparte "por argumento" cuando el titulo no alcanza | pendiente | mejora de calidad, no urgente |
| L43 | Busqueda por frase: las palabras tienen que estar cerca (NEAR), no sueltas | OK | 06/11: "chicos que juegan" ya no trae falsos positivos |
| L44 | Si no aparecen juntas, ofrecer buscar palabra por palabra | OK | chips con cada palabra en la pantalla de resultados |
| L45 | Auditor detecta plantillas sobrescritas por error | OK | 06/11: un .html con codigo Python ya no pasa la puerta |
| L46 | Si una frase no encuentra nada, sugerir temas del catalogo | OK | 06/11: "chicos que juegan" ofrece ARTE PARA CHICOS, JUEGO, TEATRO... |
| L47 | Revisar toda la busqueda con los vendedores de Rayuela | pendiente | ellos diran que frases reales usan |
| L48 | Mientras se escribe no se adivinan palabras: solo prefijos | OK | 06/11: el tipeo se corrige recien al buscar |
| L49 | Si aparece un resultado raro, pedir captura de la pantalla y el texto exacto | pendiente | para reproducirlo |
| L50 | Sugerencias de tema: palabra completa y minimo de 10 titulos | OK | 06/11: se fueron los temas basura (TAPAS de Pagina 12, TAPA DURA) |
| L51 | El vocabulario de temas del catalogo esta sucio | pendiente | TAPAS, TAPA DURA y temas de 1 titulo: limpiar en Bridge |
| L52 | Vigilante costo cero de ferias (servicio, salud y errores por Telegram) | OK | 06/11: cada 5 minutos, solo avisa si algo anda mal |
| L53 | Extender el vigilante a demo, novedades y lector | pendiente | el script ya es generico: igilar-app.sh <servicio> <nombre> <puerto> |
| L54 | Poder delegar los avisos a otra persona | pendiente | hoy es cambiar TELEGRAM_CHAT; si se quiere, bot propio y chat por app |
| L55 | Resumen horario opcional (ventas/errores) | pendiente | solo si lo piden; hoy avisa unicamente cuando algo falla |
| L56 | Caja inicial editable por admin en cualquier momento de la feria | OK | 06/11: antes solo en preparacion; ahora en abierta/cerrada tambien |
| L57 | Aviso en Caja cuando la caja inicial esta en cero | OK | 06/11: con link a los datos de la feria |
| L58 | Enriquecimiento en cadena (servicio propio, sin Bridge) | OK | 06/11: tanda tras tanda hasta terminar; log en /var/log/rayuela-enriquecido.log |
| L59 | Detener el enriquecimiento a mano | OK | crear /etc/rayuela/pausa-enriquecido |
| L60 | Vigilar que los sitios externos no bloqueen el scraping | pendiente | hoy solo se detecta por baja de aciertos |
| L61 | Camara para escanear en la pantalla de Reservas | OK | 06/11: antes solo Vender y Stock tenian camara |
| L62 | Reservas solo acepta libros cargados en la feria | OK (por diseno) | si no esta, hay que cargarlo en Stock primero |
| L63 | Control de stock en Ferias con filtro por titulo, autor, editorial o ISBN | OK | 07/11: muestra llevados, vendidos, reservados y disponibles |
| L64 | Los libros de ferias no tienen editorial cargada | pendiente | 0 de 514: el filtro por editorial existe pero no devuelve nada hasta que el dato venga de Rayuela |
| L65 | Aviso de cambios de precio colapsable y cierre por usuario | OK | 07/11: cada uno marca lo que vio; no afecta a los demas y vale en cualquier dispositivo |
| L66 | Ubicacion bloqueada para copiar el link del mapa | OK | 07/11: nginx mandaba Permissions-Policy geolocation=(); ahora (self) solo en ferias/lector |
| L67 | Mensajes de ubicacion segun el motivo (permiso, GPS apagado, demora) | OK | 07/11: antes decia siempre lo mismo |
| L68 | Reportes de cierre de feria (8 CSV + Excel con hojas) | OK | 06/11: resumen, ventas, detalle, vendidos para Rayuela, stock final, sobreventas, reservas, caja |
| L69 | Regenerar reportes despues del cierre real | pendiente | correr reportes_feria.py y reportes_xlsx.py con la feria cerrada |
| L70 | Pestana Reportes en la app con descarga por reporte, ZIP y compartir | OK | 06/11: solo admin; en celular abre el menu para mandar los CSV por WhatsApp o email |
| L71 | Probar el compartir en el celular de Vero | pendiente | Web Share con archivos: Android Chrome si; iOS Safari a veces solo comparte texto |
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
