# Inventario de UI — la tienda demo

**Este documento es la versión legible. La versión ejecutable es `demo_tienda/humo.py`.**
Si cambia una pantalla, se actualiza el humo; si el humo falla, no se publica.

| Pantalla | No puede faltar | Lo verifica el humo |
|---|---|---|
| **/** (portada) | logo, buscador, bloques de recomendados, "Lo más visto", "Seguí mirando", enlace a institucional en el pie | bloque `institucional` y `pantallas` |
| **/buscar** | resultados, facetas de editorial y temas, filtro sólo-con-stock, 5 órdenes, chips de filtros activos, paginado | bloque `busqueda` |
| **buscador del encabezado** | sugerencias con tapa y precio; corrección de errores de tipeo ("¿Quisiste decir?") | bloque `busqueda tolerante` |
| **/libro/{codigo}** | tapa, título, autor, editorial, páginas, temas, ISBN, precio, disponibilidad ("Disponible N" o "a pedido"), botón **Agregar al carrito**, consulta, **carrusel "También te puede interesar" al pie** con 3+ tarjetas, og:image con la tapa | bloque `ficha` |
| **/carrito** | tabla con cantidad (+/−), quitar, subtotal, **Total**, vaciar, aviso "esto es una demo, no hay pago", estado vacío con "Buscar un libro" y "Subir una lista". **No** debe ofrecer cierre de compra por WhatsApp | bloque `carrito` |
| **/lista** | pegar texto o subir PDF, paso de revisión con conteo de renglones, resultado con disponibilidad y tabla desplazable. **No** debe ofrecer foto hasta probarla | bloque `lista` |
| **/nosotros** | las dos sucursales (Plaza Italia 187 y La Merced 423), cómo comprar, WhatsApp | bloque `institucional` |
| **/admin** | exige clave; sin sesión redirige a /ingresar; con sesión muestra estado del catálogo y la fecha de los datos | bloque `pantallas` (protección) |
| **recursos** | `estilo.css`, logo, favicon, og-rayuela.png responden 200 | bloque `recursos` |
| **errores** | un libro inexistente devuelve 404 (no 500) | bloque `pantallas` |

## Qué se agrega antes de sumar una pantalla o un elemento

1. Añadir la obligación a esta tabla.
2. Añadir la aserción en `humo.py`.
3. Recién ahí implementar.

Así ningún cambio futuro puede quitar algo sin que la puerta lo detecte.

## Pantallas del panel (admin)

| Pantalla | Obligacion | Verificado por |
|---|---|---|
| `/admin` | abre con la clave; boton "Catálogo: ocultar y destacar"; seccion "Cómo se muestra la tienda" | humo · bloque `panel` |
| `/admin/catalogo` | buscador y filtros visibles; **sin criterio no lista nada**; boton volver al panel | humo · bloque `panel` |
| `/admin/catalogo` | ocultar y volver a mostrar funcionan (ficha 404 / 200) | prueba manual + humo `filtro del catalogo` |
| `/admin/catalogo.csv` | exporta el criterio completo | prueba manual |
| Nombres | un solo nombre por concepto: no puede haber dos secciones o botones que digan lo mismo | humo · bloque `panel` (falla si aparece "Qué se publica") |

**Regla de estilo**: antes de publicar una pantalla nueva, se revisa que no repita un concepto ya
existente en otra pantalla. Si repite, se unifica; no se agrega.
