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
| L72 | Los informes avisan adentro si falta el cierre de caja | OK | 06/11: fila en el resumen, 00-aviso.txt en el ZIP y hoja Como usar del Excel |
| L73 | Catalogo: muestra el criterio aplicado y permite aplicar al listado total | OK | 06/11: chips con boton para quitar cada criterio; check para ocultar/mostrar los N del filtro en todas las paginas |
| L74 | El humo tomaba un ISBN fijo que el admin puede ocultar | OK | 06/11: ahora el libro visible se elige de la base |
| L75 | Catalogo: el usuario elige cuantos titulos por pagina (50/100/200/500) | OK | 06/11: se conserva al filtrar y paginar; default 100 |
| L76 | En celular el listado esconde autor y editorial | OK | 06/11: menos scroll horizontal |
| L77 | Accesos "Ver la tienda" arriba en panel y catalogo | OK | 06/11: ya no hay que scrollear hasta el fondo |
| L78 | Estructura de revision UX/UI (checklist + chequeos automaticos + revisor) | OK | 06/11: auditor valida navegacion arriba y acciones antes de tablas largas |
| L79 | Corregir los hallazgos del revisor UX | pendiente | ver rayuela-docs/revision/ |
| L80 | Catalogo: condiciones guardadas de visibilidad para la web | OK | 07/11: se crean, editan y quitan; muestran cuantos titulos afectan |
| L81 | Catalogo: tildar por titulo, por pagina o todo el filtro | OK | 07/11: tildado = oculto; aplicacion masiva por SQL en ~3 s |
| L82 | Excepciones por titulo (fijar visible/oculto siempre) | OK | 07/11: las condiciones no tocan los fijados; vista Ver excepciones |
| L83 | Portada y Lo mas visto respetan los ocultos | OK | 07/11: era el bug que revivia titulos ocultos |
| L84 | Crear y aplicar la condicion de stock (menos de 2 unidades) | pendiente | decision de Jorge/Vero; la herramienta ya esta publicada |
| L85 | Verificar en produccion los 11.862 titulos ocultos de la prueba del 07/11 | pendiente | se ocultaron a mano; revisar con Ver=ocultos y volver a mostrar lo que corresponda |
| L86 | Espaciado de la tarjeta de condiciones del catalogo | OK | 07/11: padding, titulo y formulario alineados con el resto |
| L87 | Renombrar "publicables" en Estado de la tienda | pendiente | dice "publicables (incluye ocultos)"; mejor "titulos en el catalogo (visibles + ocultos)" |
| L88 | Cada ocultamiento guarda el criterio aplicado y se puede revertir | OK | 07/11: seccion "Aplicado a la web" con criterio, cantidad, fecha y boton Revertir |
| L89 | Reconstruir las condiciones viejas (600 + 11.262) sin criterio guardado | OK | 07/11: se recuperaron por lote y fecha; el criterio exacto no se guardaba antes |
| L90 | Catalogo: filtros por tapa, ficha y sinopsis | OK | 07/11: columnas con tilde en el listado y filtros combinables |
| L91 | Catalogo: vistas guardadas (combinacion completa de filtros) | OK | 07/11: se guardan desde el formulario y se abren con ?vista=ID |
| L92 | Indice de tapas y fichas (tabla archivos) | OK | 07/11: 130.789 filas; se actualiza al terminar cada tanda de enriquecimiento |
| L93 | Editorial con lista de valores para tildar (multi-seleccion) | pendiente | lo proximo del modelo autofiltro |
| L94 | Que el buscador de la web sea mejor que Bridge | pendiente | aspiracion de Jorge: mas facil, simple y completo para el vendedor |
| L95 | Un solo nombre por dato: Tapa, Sinopsis y Datos extra | OK | 07/11: se saco "ficha" de todas las pantallas del admin |
| L96 | Renombrar "ficha" en el codigo y archivos internos | pendiente | hoy queda en nombres de carpeta y funciones; no se ve en pantalla |
| L97 | Boton de traer datos dice el origen: Traer de Rayuela | OK | 07/11: aclara que no modifica nada y muestra aviso visible de pausa |
| L98 | Sincronizacion incremental de precios y stock contra Rayuela | OK (mecanica) | 07/11: validada contra el servidor de pruebas; 2 paginas 200 cambios en 1,1 s |
| L99 | Sacar la consulta a Rayuela al abrir un libro y el boton manual | OK | 07/11: la web queda servida por la base local |
| L100 | Gatillo Actualizar ahora en el panel | OK (deshabilitado) | 07/11: se habilita con SYNC_API_HABILITADA=1 y la URL de produccion |
| L101 | Activar la sincronizacion nocturna (timer) | pendiente | unidades creadas en infra/units; falta URL de produccion y autorizacion |
| L102 | Primer catch-up grande desde el 04/11 | pendiente | el tope por pasada es 2000 paginas; una sola pasada completa el atraso |
| L103 | Panel: activar/detener la sincronizacion y elegir cada cuantas horas | OK | 07/11: la automática arranca detenida |
| L104 | Panel: franja horaria opcional para la sincronizacion | OK | 07/11: el admin decide; por defecto 21-8 (regla vigente) |
| L105 | Definir con Jorge la franja y la frecuencia definitivas | pendiente | hoy: detenida, cada 2 h, franja 21-8 |
| L106 | Instalar el timer horario cuando este la URL de produccion | pendiente | unidades listas en infra/units |
| L107 | Tarjeta de sincronizacion simplificada: un solo aviso, franja desde/hasta | OK | 07/11: arranca detenida; frecuencia 2 h por defecto |
| L108 | Instalar timer y activar cuando llegue la URL de produccion | pendiente | el admin activa desde el panel |
| L109 | Filtros del catalogo reorganizados por concepto | OK | 07/11: 4 bloques, controles parejos, guardar vista separado, un solo primario |
| L110 | Filtros: grilla fija por bloque y controles de 34 px | OK | 07/11: se corrigio el conflicto de CSS que estiraba los campos al 100% |
| L111 | Capturas de UI obligatorias antes de publicar | OK | 07/11: playwright + chromium en /opt/rayuela/capturas; scripts vista_previa y capturar_ui |
| L112 | Patrones de interfaz escritos | OK | 07/11: revision/UI-PATRONES.md con alturas, grillas y prohibiciones |
| L113 | Barra superior en 1024 y 390 | OK | 07/11: enlaces sin partir, carrito compacto; capturas en revision/capturas |
| L114 | Seccion Destacados en la portada visible aunque este vacia | OK | 07/11: explica como destacar y que hace la portada mientras tanto |
| L115 | Registro de como esta quedando la web | OK | 07/11: revision/PORTADA.md con composicion, estado y capturas |
| L116 | Curar destacados para la demo | pendiente | hoy 0: la portada usa 12 al azar con tapa y stock |
| L117 | Precio minimo publicable (hay $1, $195, $295 en la portada) | pendiente | definir con Jorge/Vero y aplicar con el motor de condiciones |
| L118 | Franjas parejas en la portada (12 y 11) y "Ver todo" | pendiente | visto en la revision 07/11 |
| L119 | Busqueda del panel: usa el mismo indice que la web | OK | 07/11: antes buscaba frase exacta y fallaba con titulos invertidos ("NOMBRE DEL VIENTO, EL") |
| L120 | El catalogo no recibe titulos nuevos desde el 04/11 | pendiente | la sincronizacion esta detenida hasta tener la URL de produccion |
| L121 | Lista vacia del catalogo explica y ofrece quitar precio y stock | OK | 07/11: probado con q + stock imposible |
| L122 | Stock negativo: es de Rayuela, no de la web | OK | 07/11: Rayuela no hace inventario y ajusta al facturar. La web muestra "a pedido" y nunca el negativo; el admin lo marca para revisar |
| L123 | El catalogo del admin muestra todo por defecto | OK | 07/11: Estado "Todos" y listado sin exigir criterio; oculto es solo para el navegante |
| L124 | Arreglado error 500 al ocultar o mostrar titulos tildados | OK | 07/11: la cantidad no se calculaba en la seleccion a mano |
| L125 | Panel "Que se ve en la web" pasa debajo del listado | OK | 07/11: el listado aparece apenas se abre el catalogo |
| L126 | Autofiltro por columna en el catalogo | OK | 07/11: Stock, Tapa, Datos extra, Sinopsis y Estado con select en la cabecera; combinan con el resto |
| L127 | Precio y Editorial tambien como filtro de columna | pendiente | hoy estan en el panel de arriba |
| L128 | Mostrar stock negativo marcado en el admin | OK | 07/11: en naranja con aviso de revisar inventario |
| L129 | Autofiltro numerico con operadores en Precio y Stock | OK | 07/11: >, >=, <, <=, =, <> con valor; probado contra SQL |
| L130 | "Entre" (rango) en el autofiltro numerico | OK | 07/11: dos valores en Precio y Stock; probado stock entre 2 y 4 = 12.391 |
| L131 | Catalogo mas limpio: panel compacto, resumen en una linea y boton Aplicar | OK | 07/11: sin cajas de explicacion entre filtros y listado |
| L132 | Accion masiva verifica el total esperado antes de ocultar | OK | 07/11: incidente del catalogo entero; ver estado/INCIDENTES.md |
| L133 | Probar en copia toda accion masiva antes de publicar | pendiente | regla nueva para acciones destructivas |
| L134 | Velo de procesando en acciones del catalogo | OK | 07/11: spinner y contador al ocultar/mostrar o aplicar filtros |
| L135 | Resumen del listado aclara criterio y ofrece ver los ocultos | OK | 07/11: "mostrando 100 de 183.039 con este criterio" + enlace |
| L136 | Definir si se oculta stock <= 2 solo (422.475) o combinado con precio | pendiente | decision de Jorge/Vero |
| L137 | Selector Y/O para combinar criterios del catalogo | OK | 07/11: default O; con precio<=15000 O stock<=2 = 423.458 |
| L138 | Confirmar con Jorge antes de ocultar por O (423.458 = casi todo) | pendiente | accion destructiva enorme |
| L139 | Buscador y editorial acotan siempre (no entran en el Y/O) | OK | 07/11: Y/O solo combina filtros de columna; biodesco+stock>0 = 6 |
| L140 | Revisar si conviene revertir la ultima tanda de 408.069 ocultos | pendiente | decision de Jorge |
| L141 | Scrapeo independiente de la visibilidad de la tienda | OK | 07/11: sin filtro=0; probado con un libro oculto que igual se proceso |
| L142 | Registro de intentos por titulo y fuente | OK | 07/11: tabla intentos_enriquecido; no se repiten los sin_datos en todas las fuentes |
| L143 | Prototipo CLIP + OCR para buscar por tapa | pendiente | aprobado para probar con 100 tapas antes de procesar todo |
| L144 | Prototipo CLIP de busqueda por tapa | OK | 07/11: MobileCLIP2-S0, 0,11 s/tapa, pico 916 MB; foca/elefante acierta |
| L145 | Indexar todas las tapas de titulos con stock | pendiente | 25.731 tapas ~47 min; definir si tambien las 63.833 |
| L146 | OCR de tapas con tesseract (spa/eng) | pendiente | para buscar "English 3" y texto visibles |
| L147 | Evaluar descripcion de tapas con IA (US$25-75) si CLIP no alcanza | pendiente | fase 2 de busqueda por imagen |
| L148 | Evaluar agregar swap al VPS (hoy no tiene) | pendiente | el pico de CLIP es 916 MB sobre 2 GB |
| L149 | Busqueda por tema: cuenta palabras dentro de TEMA1-3 | OK | 07/11: "duelo" sugiere Duelo (17) aunque cada combinacion exacta sea distinta |
| L150 | Sincronizar categoria y rubro desde Bridge | pendiente | endpoints /categorias y /rubros andan en pruebas; categoria_id hoy vacio |
| L151 | Campo temas_extra derivado de sinopsis externas, sin pisar temas de Rayuela | pendiente | para busqueda y relacionados, como ultimo recurso |
| L152 | Relacionados: usar temas de Rayuela, luego rubro, luego temas_extra | pendiente | nunca reemplazar la curaduria de Rayuela |
| L153 | Export de Bridge analizado: trae Rubro y Categoria, no TEMA1-3 | OK | 07/11: ver estado/EXPORT-BRIDGE.md |
| L154 | Sincronizar rubro/categoria/stock/precio/detalle por API v1 en bloque | pendiente | 200 por pagina, ~15 min el catalogo completo |
| L155 | Pedir export de Bridge con TEMA1/TEMA2/TEMA3 si el listado lo permite | pendiente | evita el sync lento de atributos |
| L156 | Script de sync por API v1 (rubro, categoria, stock, precio, detalle_bridge) | OK (pruebas) | 07/11: 400 filas validadas contra el servidor de pruebas; 6,5 s por pagina |
| L157 | Correr sync completo cuando Luis pase la API de produccion | pendiente | ~2.248 paginas; avance guardado en sync_estado |
| L158 | Usar rubro/categoria en busqueda, relacionados y filtros del admin | pendiente | depende del sync |
| L159 | Definir regla de sinopsis: detalle_bridge vs detalle externo | pendiente | Bridge suele traer detalle corto; el externo es largo |
| L160 | Registro de busquedas: termino, resultados y clic | OK | 07/11: columnas resultados/posicion en eventos; clic ligado a la ultima busqueda |
| L161 | Informe de busquedas en la pestana Estado | OK | 07/11: 30 dias, top, sin resultados, clics y % clic |
| L162 | Enriquecimiento libera la base cada 5 titulos | OK | 07/11: dejaba una transaccion abierta minutos y bloqueaba migraciones |
| L163 | Equivalencias de terminos modernos (amigurumi, estoicismo) | pendiente | construirlas a partir de busquedas sin resultados y clics |
| L164 | Proponedor de equivalencias desde busquedas (sesion y tipeo) | OK | 07/11: probado en copia; amigurumi->tejido, borgs->borges |
| L165 | Equivalencias aprobadas aplicadas al buscador | OK | 07/11: suma resultados del destino y muestra aviso |
| L166 | Aprobar/rechazar equivalencias desde Catalogo > Estado | OK | 07/11 |
| L167 | Poner en cero el registro de busquedas (todo o hasta fecha) | OK | 07/11 |
| L168 | Correr el proponedor periodicamente (cron diario) | pendiente | despues de ver algunos dias de busquedas |
| L169 | Proponedor usa el tema del libro clickeado | OK | 07/11: amigurumi -> costura y tejido; exige 2 sesiones |
| L170 | Timer diario del proponedor (03:30) | OK | 07/11: rayuela-equivalencias.timer |
| L171 | Detectar vocabulario que cambia y limpiar equivalencias viejas | pendiente | el proponedor lee 90 dias; falta medir uso de las aprobadas |
| L172 | Demanda registrada en Estado: 7/30 dias, en alza, coincidencias con stock | OK | 07/11: numeros, sin recomendaciones |
| L173 | Guardar resumen diario de busquedas para historia larga | pendiente | hoy se lee la tabla eventos; conviene agregado diario |
| L174 | Marcar acontecimientos (premios, efemerides) para cruzar con la demanda | pendiente | opcional, solo numeros |
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
