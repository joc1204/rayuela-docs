# Modelo del negocio de Rayuela (para entender los datos de Bridge)

Escrito a partir de lo que explicó Jorge (03/11/2026). **Es la fuente de verdad
conceptual**: si el código o la API contradicen esto, gana esto.

## 1 · Precio

- **No hay precio impreso en el libro.** "Precio de tapa" es el nombre que se le da al
  **precio único de venta al público (PVP)** que fija la editorial.
- Por ley el precio es **estandarizado**: la librería **no puede publicar un precio
  distinto** al indicado. No hay descuentos sobre el PVP (salvo una "oferta" que
  publique Rayuela, decisión comercial).
- **Un libro = un precio.** No hay "precio sin IVA" y "precio con IVA": los libros están
  **exentos de IVA**. Todo el circuito de un ERP que discrimina IVA (listas, comprobantes,
  reportes) presenta números que para una librería no significan nada.
- El **descuento del proveedor no afecta el precio al público**: es el margen de Rayuela
  sobre la factura total del proveedor/editorial, no un descuento al cliente.

### Implicaciones para nuestra integración

- Mostrar siempre el **PVP** que informa Bridge (`precioVenta`). Nunca calcular precio
  desde costo ni aplicar IVA.
- No usar `markup`, `descuentoHabitual`, `precioCosto` para libros: no aplican.
- Si en el futuro Rayuela publica una oferta, es una **decisión comercial explícita**
  (campo propio nuestro), no un cálculo sobre el precio de Bridge.

## 2 · Consignación (cupo)

- La consignación es un **cupo**: se incrementa cuando la editorial manda material con
  **remito en consignación**, y se descuenta cuando la librería devuelve material físico
  o cuando la editorial lo cobra con una **factura de baja de consignación**.
- Para nosotros **no cambia nada del precio** ni del catálogo: el material consignado
  **está disponible para vender**.

## 3 · Stock disponible

Lo que nos importa publicar como "disponible" es **lo que se puede vender**:

- El stock físico puede estar afectado por **reservas de clientes**: Rayuela reserva
  pedidos; cuando el libro entra queda reservado y **se descuenta del stock** para que no
  se venda a otro.
### Verificado (03/11/2026)

Contrastado contra la pantalla de artículos de Bridge:

| ISBN | Libro | Sistema: Actual | Sistema: Disponible | API `stockVenta` |
|---|---|---|---|---|
| 7705969463523 | ILIADA Y ODISEA (estuche) | 2 | 2 | **2** (coincide) |
| 7798083708649 | CORAZON DE LO SAGRADO | 1 | 1 | **1** (coincide) |
| 9789876284509 | SIGLO DE PERON, EL (con reserva) | 2 | 1 | **1** (coincide) |

**Conclusión: `stockVenta` de la API es el "Disponible" del sistema, ya con las reservas
descontadas.** No hay que restar nada: lo que devuelve la API es exactamente lo que se
puede vender.

Otros datos que confirma la misma pantalla:

- Los libros figuran con alícuota "( %0,0 ) EXENTO" y `precioLista = precioVenta`
  (un solo precio, sin IVA).
- El material en consignación cuenta como stock vendible.
- El libro reservado muestra "Actual 2 / Disponible 1": la reserva no aparece en el
  stock de la API, ya está aplicada.

## 4 · Qué implica para el catálogo público (bot / web)

| Dato | Regla |
|---|---|
| Precio | PVP de Bridge, tal cual. Sin IVA, sin descuentos calculados |
| Disponible | "se puede vender" (stock físico − reservas, según verificación) |
| Sin stock | **No se oculta**: se publica como "sin stock / a pedido". El título debe existir |
| Consignación | Es stock vendible: no se distingue al público |
| Títulos a excluir | Los que no son libros (señaladores, amigurumis, códigos, bienes de uso) o sin datos fundamentales |

## 5 · Por qué Bridge fue un problema

Bridge es un ERP multiempresa. Rayuela es su **única librería de textos**, así que las
particularidades del rubro (exención de IVA, PVP único, consignación) se resolvieron como
**parches**: campos "propiedades" hechos a mano (AUTOR, COLECCION, TEMA1-3, PAGINAS,
**AGOTADO DESDE**). Por eso la API "genérica" nueva (v1) no trae esos campos: no son
parte del modelo estándar del producto.
