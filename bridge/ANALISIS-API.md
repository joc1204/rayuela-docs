# Bridge · Lo que se descubrió probando la API documentada (vieja)

**Fecha:** 03/11/2026
**Base:** `http://rayuela1.serveftp.net:9090/BSGestion`
**Estado:** la versión vieja funciona **sin token** hoy; cuando Bridge actualice el BS (año
que viene, según Luis) va a pedir el mismo token que la nueva.

> Todo lo de abajo se probó en vivo contra el servidor de Rayuela.

## Endpoints útiles verificados

| Qué necesitamos | Endpoint | Resultado |
|---|---|---|
| Ficha completa por ISBN | `GET /rest/webservice/articulo/{isbn}` | ✅ Devuelve **todo** (ver campos abajo) |
| Solo precio | `GET /rest/webservice/articulo/{isbn}/precio` | ✅ `{"codigo","moneda","precioLista"}` |
| Solo stock | `GET /rest/webservice/articulo/{isbn}/stock` | ✅ `{"codigo","stockVenta"}` |
| Solo imagen | `GET /rest/webservice/articulo/{isbn}/imagen` | ✅ **base64 de un JPEG** |
| Precios modificados desde fecha/hora | `GET /rest/webservice/articulos/precio/{anio}/{mes}/{dia}/{HHmm}/{pagina}` | ✅ lista `codigo, moneda, precioLista` |
| Stock modificado desde fecha/hora | `GET /rest/webservice/articulos/stock/{anio}/{mes}/{dia}/{HHmm}/{pagina}` | ✅ lista `codigo, stockVenta` |
| Artículos nuevos desde fecha | `GET /rest/webservice/articulos/nuevos/{anio}/{mes}/{dia}/{HHmm}/{pagina}/{propiedades}` | ✅ ficha completa |
| Rubros / Categorías / Marcas | `/rest/webservice/rubros`, `/categorias`, `/marcas` | ✅ id → nombre |
| Crear reserva en Bridge | `POST /rest/webservice/comprobante/reserva` | documentado, sin probar |

## Campos de la ficha (`articulo/{isbn}`)

```
categoria (id) · codigo · descripcion · detalle (SINOPSIS) · estado ("A Comprar")
fechaAct · fechaActCosto · fechaActImagen · fechaCre · fechaMod
idMarca · marca · moneda · precioLista · stockVenta
imagen: ["<base64 JPEG>"]        ← la tapa, incrustada
propiedades: [{nombre, valor}]   ← AUTOR, EDICION, REEDICION, COLECCION,
                                   TEMA1..3, ILUSTRADOR, TRADUCTOR, PROLOGO,
                                   IDIOMA, PESO, FORMATO, PAGINAS, AGOTADO DESDE
```

Ejemplo real (`9789875802872`): `detalle` trae la contratapa completa de "Lo pasado
pensado"; propiedades con AUTOR, EDICION, REEDICION, COLECCION y TEMA1-3.

## Limitaciones observadas

- **Máximo 100 registros por página** en los listados → hay que paginar hasta que
  devuelva menos de 100.
- La ficha trae la imagen **incrustada** (30-45 KB de base64): para consultas
  frecuentes conviene `/precio` y `/stock` por separado.
- `detalle` puede traer `\r\n` (limpiar antes de mostrar).
- `GET /rest/productos/{vendedor}/{modulo}/{fecha}` → **404** en esta instalación.
- Sin token hoy. Diseñar con el token **en configuración desde el día uno**, porque
  la versión nueva lo pide y la vieja lo va a pedir al actualizarse.

## Qué cambia en el plan

Antes (con el endpoint no documentado): había que **scrapear** tapas y sinopsis.

Ahora, con la API documentada:

| Dato | Fuente |
|---|---|
| Precio, stock | API (incremental por fecha) |
| Título, autor, editorial (marca), colección | API (ficha) |
| Sinopsis | API (`detalle`) |
| Tapa | API (`imagen` base64) |
| Rubro / categoría / tema | API (`rubros`, `categorias`, `propiedades.TEMA*`) |
| Público / edad / nivel de lectura | **Nuestro** (clasificación automática + curaduría) |
| Ventas propias, listas, premios | **Nuestro** |

**Se elimina casi todo el scraping del catálogo.** Queda solo para completar lo que la
API no trae (clasificación por público/edad) o libros con `detalle` o `imagen` vacíos.

## Pendiente de la reunión con Luis / documentación nueva

1. Token de la **API nueva**: cómo se obtiene y si hay entorno de prueba
2. **Frecuencia de consulta** permitida (los de Berisso consultaban periódicamente)
3. Si la API nueva expone **sinopsis y tapa** igual que la vieja
4. Si hay endpoint de **ventas** (para volcar desde la feria) o si solo reservas
5. Qué significan los valores de `estado` ("A Comprar", etc.)

---

## Ampliación (misma fecha): los 5 tipos de cambio y el tamaño real

Probados los cinco tipos del listado incremental:

| Tipo | Qué devuelve | Uso |
|---|---|---|
| `precio` | `codigo, moneda, precioLista` | sync de precios (liviano) |
| `stock` | `codigo, stockVenta` | sync de stock (liviano) |
| `imagen` | `codigo, imagen[]` (base64) | detectar tapas nuevas/cambiadas |
| `propiedades` | ficha completa (con `detalle`, `imagen`, `propiedades`) | trae metadatos + sinopsis |
| `atributos` | `codigo, descripcion, propiedades[]` (SIN imagen) | **el mejor para metadatos**: liviano |

**El filtro por fecha/hora funciona** (verificado: distintas fechas devuelven distinto
primer registro).

### Tamaño del catálogo (importante)

Tope de 100 registros por página. Muestreo:

- `articulos/precio/{...}/1..1999` devuelve 100 en cada página; la 2000 devuelve 0
  → **~190.000-200.000 artículos** con precio cambiado desde enero 2026
- `articulos/nuevos/1900/.../3000` todavía devuelve 100
  → **más de 300.000 artículos** en la historia del sistema

Consecuencia: **no se puede "bajar todo" de una vez**. El diseño tiene que ser por capas:

1. **Sync liviano** (cada X minutos): `articulos/precio` y `articulos/stock` desde la
   última marca de agua → pocas páginas.
2. **Ficha por ISBN bajo demanda** (`articulo/{isbn}`): se cachea local. Evita traer
   imágenes de 300.000 artículos.
3. **Relleno progresivo** (de noche): `articulos/atributos` y `articulos/imagen` por
   tandas, para los libros que nos interesan (por ejemplo, los de la librería).
4. **Primera carga**: arrancar por los ISBN que ya tenemos + los que pide el bot,
   no por el catálogo completo.

### Pregunta clave para Luis

¿Existe una **exportación masiva** (dump/CSV) del catálogo? Si existe, la primera carga
se resuelve en una descarga en vez de miles de consultas paginadas.
---

# API REST v1 (la nueva, septiembre 2026)

Documentación leída completa (8 páginas). **Lo que cambia respecto de la vieja:**

| | v0 (vieja, documentada) | v1 (nueva) |
|---|---|---|
| Transporte | HTTP | **HTTPS** |
| Autenticación | sin token (hoy) | **Bearer token** estático por sistema |
| Listado | artículos modificados **desde fecha/hora** (100/pág) | catálogo paginado (50/pág, base 0) — **sin filtro por fecha** |
| Campos | ficha fija + `propiedades[]` | **`campos=` seleccionable** (36 campos) |
| Búsqueda | no | `busqueda=` por descripción |
| Código de barras | no | **`codigoBarras` + `codigosBarras[]`** |
| Estado/discontinuado | `estado` | `estado` + `ventaDiscontinua` / `compraDiscontinua` |
| Clasificación | ids de rubro/categoría/marca | **nombres + ids** de rubro, categoría, marca, familia |
| Precios | `precioLista` | `precioVenta`, `precioLista`, `precioVentaSIVA`, costos, alícuota, descuentos, markup |
| Stock | `stockVenta` | `stock`, `stockMinimo/Maximo/Optimo` |
| **Tapa (imagen)** | **sí (base64)** | **no** |
| **Propiedades de libro** (AUTOR, COLECCION, TEMA1-3, PAGINAS…) | **sí** | **no** |
| Reservas / ventas | reserva (POST) | no documentado |

**Conclusión: las dos se complementan.** v1 para enumerar el catálogo, precios de venta,
estado y códigos de barras; v0 para tapas, sinopsis, propiedades de libro y cambios
incrementales.

## Estado real hoy (probado)

- `http://rayuela1.serveftp.net:9090/BSGestion/rest/...` (v0) → **funciona**
- `.../BSGestion/api/productos` (v1) → **404** en ese servidor
- HTTPS en 9090 / 443 / 8443 → no responde

→ **La v1 todavía no está publicada en la instalación de Rayuela.** Hay que pedirle a
Luis la URL real (host y puerto) y confirmar que el token `api__…` es para ese entorno.

## Cómo se resuelve "todos los títulos" (bot 24/7 y web)

1. **Enumeración completa (v1)**: `productos?campos=codigo,descripcion,precioVenta,
   moneda,estado,ventaDiscontinua,categoria,marca,codigoBarras&pagina=N` — 50 por página.
   Con un catálogo de ~200.000 son ~4.000 pedidos: una carga inicial de 1-2 horas y
   luego una pasada diaria o semanal.
2. **Cambios frecuentes (v0 incremental)**: `articulos/precio` y `articulos/stock` desde
   la última marca de agua, cada 15-30 minutos (liviano).
3. **Ficha rica (v0)**: `articulo/{isbn}` bajo demanda y cacheada: tapa, sinopsis,
   AUTOR/COLECCION/TEMAS. Se pide solo para los libros que se muestran.
4. **Filtro de "títulos disponibles"** (decidido por nosotros, no por Bridge):
   - `ventaDiscontinua = false`
   - `estado` válido (a definir con Luis qué códigos significan "activo")
   - `codigo` o `codigoBarras` con forma de ISBN (13 dígitos que empiezan en 978/979)
   - `descripcion` no vacía y `precioVenta > 0`
   - **sin stock NO se descarta**: el título queda publicado como "sin stock / a pedido"

## Preguntas para Luis

1. **URL y puerto reales de la v1** para Rayuela, y si el token recibido es de ese entorno.
2. ¿La v1 puede devolver **`imagen`** y las **propiedades de libro** (autor, colección,
   temas)? Si no, seguimos usando la v0 para eso.
3. ¿Hay en la v1 un endpoint de **modificados desde fecha** (como la v0) o hay que
   reenumerar el catálogo completo cada vez?
4. ¿**Frecuencia máxima** de consultas y si existe una **exportación masiva** (CSV/dump)
   para la primera carga.
5. ¿Hay endpoints de **ventas** o solo de **reservas**?
6. ¿Qué significan los valores de **`estado`** y qué identifica a un artículo "activo"?
---

## Corrección (03/11/2026): la v1 no está publicada en el servidor de Rayuela

Prueba de puertos y protocolos sobre `rayuela1.serveftp.net`:

| Puerto | Estado | Protocolo | Resultado de `/BSGestion/api/productos` |
|---|---|---|---|
| 80 | cerrado | — | — |
| 443 | abierto | **HTTP plano** (no TLS: "wrong version number") | HTTP 404 |
| 9090 | abierto | HTTP | HTTP 404 (v0 sí responde en `/rest/webservice/...`) |
| 8080, 8081, 8443, 9000, 9091, 9092, 9443 | cerrados | — | — |

**Conclusión:** la v1 (`https://[servidor]/BSGestion/api`) **no está instalada en la
instalación de Rayuela**. Coincide con lo que dijo Luis: "cuando se actualice la versión
del BS te va a pedir el mismo token" → la v1 viene con la versión nueva del sistema, que
todavía no está puesta acá o está en un servidor de Bridge.

**Falta:** que Luis pase la **URL real** (host y puerto) del entorno donde la v1 está
publicada, y si ese servidor es de Bridge o de Rayuela.

## Decisión de diseño (para no quedarse esperando)

Construir la integración contra la **v0 documentada** (que funciona hoy y tiene: precio,
stock, tapa, sinopsis, propiedades de libro e incrementales), con una **capa de
adaptador** que permita enchufar la v1 cuando esté disponible (para códigos de barras,
`ventaDiscontinua`, nombres de clasificación y precios con IVA).