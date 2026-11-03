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

## 2 · Stock disponible (lo único que nos importa)

- El único dato que usamos es el **stock disponible: lo que se puede vender**, tal cual
  lo informa el sistema.
- **La consignación no incumbe al catálogo**: es un cupo administrativo entre Rayuela y la
  editorial. No se menciona, no se distingue y no se muestra.
- Lo que el sistema llama "Disponible" **ya tiene descontadas las reservas** de clientes:
  un libro reservado no se ofrece como disponible.

### Verificado contra el sistema (03/11/2026)

| ISBN | Libro | Sistema: Actual | Sistema: Disponible | API `stockVenta` |
|---|---|---|---|---|
| 7705969463523 | ILIADA Y ODISEA (estuche) | 2 | 2 | **2** (coincide) |
| 7798083708649 | CORAZON DE LO SAGRADO | 1 | 1 | **1** (coincide) |
| 9789876284509 | SIGLO DE PERON, EL (con reserva) | 2 | 1 | **1** (coincide) |

**Conclusión: `stockVenta` de la API es el "Disponible" del sistema, con las reservas ya
descontadas.** No hay que restar nada: lo que devuelve la API es exactamente lo que se
puede vender.

La misma pantalla confirma que los libros figuran con alícuota "( %0,0 ) EXENTO" y
`precioLista = precioVenta` (un solo precio, sin IVA).

## 3 · Qué implica para el catálogo público (bot / web)

| Dato | Regla |
|---|---|
| Precio | PVP de Bridge, tal cual. Sin IVA, sin descuentos calculados |
| Disponible | Lo que informa el sistema como "Disponible" |
| Sin stock | **No se oculta**: se publica como "sin stock / a pedido". El título debe existir |
| Títulos a excluir | Los que no son libros (señaladores, amigurumis, códigos, bienes de uso) o sin datos esenciales |

## 4 · Por qué Bridge fue un problema

Bridge es un ERP multiempresa. Rayuela es su **única librería de textos**, así que las
particularidades del rubro (exención de IVA, PVP único, stock vendible con reservas) se
resolvieron como **parches**: campos "propiedades" hechos a mano (AUTOR, COLECCION,
TEMA1-3, PAGINAS, **AGOTADO DESDE**). Por eso la API "genérica" nueva (v1) no trae esos
campos: no son parte del modelo estándar del producto.
