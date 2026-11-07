# Exportación de Bridge (Listado de Artículos) — análisis

Archivo analizado: `Listado_Artículos_071120261341.csv` (búsqueda "borges").
99 filas con código, 98 códigos únicos.

## Columnas del export y a qué corresponden

| Export | Nuestra base | Notas |
|---|---|---|
| `Codigo` | `productos.codigo` | ISBN; una fila del export no tenía código |
| `Descripcion` | `productos.descripcion` | |
| `Rubro` | **falta** (`rubro`) | clasificación amplia: LITERATURA GENERAL, INFANTILES… |
| `Categoría` | **falta** (`categoria`) | más fina que rubro: LITERATURA ARGENTINA, NOVELA GRAFICA… |
| `Marca` | `productos.marca` | 50 de 99 vienen "SIN CONSIGNAR" |
| `Estado` | `productos.estado` | A Comprar (89), Finalizado (6), Agotado (4) |

El export **no trae** TEMA1/TEMA2/TEMA3, stock, precio, sinopsis ni tapa.

## Rubro y Categoría son campos distintos

En 6 de 99 filas difieren. Ejemplo:

```
9788494731020  BORGES            rubro=LITERATURA GENERAL  categoría=NOVELA GRAFICA
9789500445214  BORGES            rubro=LITERATURA GENERAL  categoría=LITERATURA ARGENTINA
```

Rubro = estante amplio; Categoría = clasificación fina. Nuestro campo `temas`
(TEMA1-3) es una **tercera taxonomía**, también de Rayuela, y no reemplaza a ninguna
de las dos. Ejemplo del mismo export:

```
9789500445214  export: LITERATURA GENERAL / LITERATURA ARGENTINA
               nuestra base: temas = "CHARLAS, CONVERSACIONES"
9788494731020  export: LITERATURA GENERAL / NOVELA GRAFICA
               nuestra base: temas vacío
```

## Estado de esos 99 títulos en nuestra base

| Dato | Cantidad |
|---|---|
| en la base | 99 |
| publicables | 94 |
| con stock | 6 |
| visibles hoy | 5 |
| con temas | 26 |
| con sinopsis | 8 |

La mayoría de los resultados de "borges" son títulos sin stock: no son material
vendible hoy, pero sí curaduría que conviene conservar.

## Hallazgo: la API v1 permite traer rubro, categoría, stock, precio y sinopsis en bloque

Probado con token en el servidor de pruebas:

```
GET /api/productos?pagina=1&limite=200&campos=codigo,descripcion,categoria,rubro,stock,precio,detalle,autor,marca,coleccion,estado
```

Devuelve los nombres de rubro y categoría, el stock, el precio, el detalle (sinopsis),
autor, marca y estado. Límite 200 por página, 449.499 registros → **~2.250 páginas,
≈15 minutos a 3 pedidos/s**.

TEMA1-3 **no** salen por la API; siguen viniendo del webservice viejo
(`/articulos/atributos`, que es lento) o de un export que los incluya.

## Conclusión

- El export sirve para validar el mapeo de **rubro/categoría/estado/marca**.
- La API v1 sirve para sincronizar en bloque rubro, categoría, stock, precio y
  sinopsis sin tocar temas.
- Los temas de Rayuela se mantienen aparte y no se pisan con datos externos.
