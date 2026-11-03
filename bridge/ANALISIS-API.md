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