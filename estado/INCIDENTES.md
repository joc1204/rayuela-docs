# Incidentes

## 07/11/2026 — Se ocultó el catálogo entero (428.674 títulos)

**Qué pasó.** Desde el Catálogo, con el filtro *Precio <= 15.000* y *Stock <= 2*
(183.039 títulos), se tocó "Tildar los 183.039", luego **Ocultar** y se confirmó.
El sistema ocultó **428.674**: todo el catálogo.

**Causa.** El formulario de la acción masiva no enviaba los filtros nuevos
(operadores de precio y stock, tapa, datos extra, sinopsis, estado). El servidor
reconstruía el criterio solo con los filtros viejos y le quedaba "todo el catálogo".
Es decir: la pantalla mostraba un conjunto y la acción se aplicaba a otro.

**Restauración.** Se revirtió inmediatamente:

```
ocultos antes:  428.674
ocultos después:      0
visibles:       428.674
```

Respaldo previo a la reversión:
`/root/respaldos-catalogo/catalogo-antes-revertir-todo-20261107-0301.db`

**Arreglo.**

1. El formulario de la acción masiva ahora envía **todos** los filtros
   (incluidos los operadores numéricos y las condiciones de columna).
2. El servidor compara el **total esperado** (el que se veía en pantalla) con el
   total que devuelve el filtro en ese momento. Si no coinciden, **no oculta nada**
   y avisa: "El filtro cambió desde que se cargó la página".
3. Verificado en copia: con el filtro real, la acción ocultó exactamente
   **183.039**; con un total manipulado, ocultó **0**.

**Lección.** Toda acción destructiva masiva tiene que viajar con el criterio y con
el total que el usuario vio, y el servidor tiene que verificarlos antes de escribir.
