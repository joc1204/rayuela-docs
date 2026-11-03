# Rayuela · Plan de módulos (actualizado 03/11/2026)

Decisiones tomadas con Jorge. Lo que está acá está **aprobado**; lo que no, es propuesta.

## Estado de la infraestructura

| Ambiente | URL | Qué es |
|---|---|---|
| Producción | `https://ferias.rayuelalaplata.com.ar` | App real de ferias (puerto 5050) |
| Prueba | `https://prueba.rayuelalaplata.com.ar` | Misma app, base copiada, cartel violeta "AMBIENTE DE PRUEBA" (puerto 5051) |
| Lector cliente | `https://lector.rayuelalaplata.com.ar` | Consulta de precios, público |
| Lector vendedor | `https://lector.rayuelalaplata.com.ar/?m=v` | Con ficha completa y "Armar lista" |
| Apex | `rayuelalaplata.com.ar` | **Sin registro DNS** hasta que exista el portal |

- Refrescar datos de prueba con los reales: `/root/refrescar-prueba.sh`
- Dominio en Cloudflare (DNS only, sin proxy). Certificados Let's Encrypt con renovación automática.
- Regla: **nada se instala en producción sin pasar por `prueba.`**

## Módulos aprobados

### 1 · Lector con horario (1 día)
- Horario: **una franja por día**, días configurables (la librería no cierra al mediodía)
- Corte por inactividad **configurable** (hoy fijo en 30 min)
- Cierre extendido para el día (eventos: charlas, presentaciones)
- **El corte no borra la lista**: se guarda en el navegador y sobrevive a la recarga; fuera de horario no se escanea pero la lista queda y se puede copiar/enviar por WhatsApp
- PIN para el modo vendedor (hoy está abierto)
- Prioridad: lector **cliente**

### 2 · Encabezado y pie del mensaje configurables (0,5 día)
- Dos cajas de texto en el panel + vista previa + "restaurar por defecto"
- Si el servidor no responde, el lector usa los textos de fábrica
- Cuidado: subir `?v=` en cada cambio (caché de celulares)

### 3 · Búsqueda del tesoro (1 día + 0,5 tarjetas)
- Tesoros múltiples e independientes
- Campos por tesoro: ISBN, premio (texto libre), pista opcional, unidades totales,
  **unidades por tarjeta** (el resto se gana escaneando), ámbito local/feria/ambos,
  vigencia desde/hasta, WhatsApp de confirmación
- **Dos vías conviven**: escaneo del ISBN (con formulario nombre + DNI) y **tarjetas
  físicas con código** escondidas en los libros (las carga el vendedor en el panel)
- Contador compartido y atómico: al llegar a 0 el tesoro se cierra solo
- Registro de ganadores: origen (escaneo/manual/tarjeta), usuario que registró, nota, entregado
- **Sin regla antifraude por DNI**: hay confianza y cercanía con los clientes. Sí se evita
  el doble envío accidental (mismo DNI + mismo tesoro)
- Tarjetas: código legible + QR del mismo código, para tipear o escanear en el mostrador

### 4 · Listas guardadas (2 días)
- Botón nuevo en el lector cliente, **sin tocar** Copiar y WhatsApp
- Pide: nombre, apellido, DNI, cumpleaños, correo + consentimiento
- **Dos formas de verla**:
  - **En el local**: el vendedor busca por DNI o apellido en el panel, marca lo que se lleva
    y anota el **número de voucher** (pago manual, Bridge no lo contempla)
  - **Link compartible** (pedido de Verónica): el cliente recibe un link con código no
    adivinable para pasar a familiares/amigos que están lejos (caso estudiantes del interior).
    La página pública muestra **título, autor y tapa — SIN precios**, y marca qué ya está
    **cumplido/regalado**. Sin indexar.
- Sin precios en el link: evita que el catálogo se compare o quede desactualizado
- Un ítem cumplido se marca con fecha; no se identifica al que compró

### 5 · Docentes y listas de material (a dar forma — gancho comercial)
- Objetivo: no solo administrar la lista de material de un curso, sino **darle una utilidad
  al docente** para que recomiende Rayuela a los padres
- Ideas a definir: lista del curso cargada por el docente o por Rayuela, link para el grupo
  de padres, disponibilidad en stock, reserva del kit, impresión de la lista, aviso cuando
  llega lo que falta
- Pendiente: reunión con docentes y definir el gancho concreto

### 6 · Panel en módulos (1 día, junto con el 1)
- Dashboard con interruptor por módulo y una pantalla por módulo
- Módulos apagados no aparecen en el lector
- Secciones: Ferias y ventas · Catálogo · Lector · Tesoro · Listas · Difusión · Usuarios · Sistema
- Objetivo: ordenado, minimalista, claro

### 7 · Correo de Novedades con dominio propio — HECHO 03/11/2026
- Proveedor: **Resend** (Brevo se descartó: pedía verificación por SMS que nunca llegaba)
- Remitente `Rayuela Libros <novedades@rayuelalaplata.com.ar>`
- DKIM + SPF verificados; falta agregar DMARC (`TXT _dmarc = v=DMARC1; p=none;`)
- Probado desde el código del bot: llega a la bandeja de entrada
- Deja de depender del Gmail personal de Jorge

### 8 · Difusión por mail (futuro)
- Listas por rubro/público con consentimiento, usando Brevo
- WhatsApp masivo NO: requiere API Business, plantillas y opt-in

## Datos y arquitectura (propuesta, esperando doc de la API)

- Réplica local del catálogo + **enriquecimiento** de campos faltantes (tapa, sinopsis,
  clasificación por público/tema, embeddings para búsqueda semántica)
- Regla: un dueño por campo — Rayuela manda precio/stock; nosotros completamos lo que falta
- Con la réplica, el lector responde local y no depende del Bridge en vivo
- DNI = número de cliente en Bridge → clave natural para listas y ganadores

## Riesgos a respetar

1. **La feria manda**: el viernes 6 no se toca nada. Lector congelado desde el jueves.
2. Cambios de estáticos no requieren reinicio; cambios de plantillas sí (evitar en feria).
3. Subir siempre `?v=` en los estáticos del lector (caché de celulares).
4. Migraciones de base: aditivas (`CREATE TABLE IF NOT EXISTS`) + respaldo previo.
5. Todo módulo nuevo nace **apagado**.

## Pendientes de infraestructura

- Sacar el nombre temporal `201.32.132.197.sslip.io` cuando se confirme el uso en celulares
- Repo de documentos (manuales, guía de novedades, documento del servidor, QRs)
- `salud.sh`: revisa servicios, disco, HTTPS y backups; avisa por mail si algo falla
- Limpiar `_deploy_ferias` (scaffolding de despliegue) del workspace
