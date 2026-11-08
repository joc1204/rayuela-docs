# Dependencias verificadas con el sistema de Rayuela (Bridge)

**Actualizado:** 04/11/2026 21:55 · **Método:** lectura del código desplegado en el VPS, no de memoria.
Cada fila tiene el archivo y la línea que lo respalda.

## Mapa

| Componente | Endpoint / acción | Archivo:línea | Token | Si la REST se cae |
|---|---|---|---|---|
| **App de ferias (y autoconsulta del lector)** | `BuscadorProductosAction.do?method=buscarArticulo` | `/opt/rayuela/ferias/rayuela.py:11` (usado desde `app.py:333, 517, 704, 766`) | **No** | **Sigue funcionando** |
| Demo: ficha bajo demanda | `/rest/webservice/articulo/{isbn}` | `/opt/rayuela/demo/app.py:40` (base) y `:285` | Sí (desde 04/11) | No funciona |
| Demo: sincronización (precios, metadatos) | `/rest/webservice/articulos/...` vía `sincronizar.traer` | `demo/sincronizar.py` (1 referencia); lo usan `metadatos.py` y `sincronizar_rapido.py` (0 referencias directas: llaman a `traer`) | Sí | No funciona |
| Demo: stock por libro | `/rest/webservice/articulo/{isbn}/stock` | `demo/stock_publicados.py` (2 referencias) | Sí | No funciona |
| Demo: fichas completas | `/rest/webservice/articulo/{isbn}` | `demo/fichas_nocturnas.py` (3 referencias) | Sí | No funciona |
| Demo: tapas | `/rest/webservice/articulo/{isbn}/imagen` | `demo/tapas_publicadas.py` (2 referencias) | Sí | No funciona |
| **Novedades / scraper** | sitios de terceros (zivals, yenny, sbs) | `/opt/rayuela/novedades/novedades/sitios.py` | No aplica | **Sigue funcionando** |
| Reclamo de tapas externas | sitios de terceros | `demo/tapas_externas.py` | No aplica | **Sigue funcionando** |

## Conclusión operativa

- **La librería no perdió ninguna función**: la app de ferias y la autoconsulta usan el buscador web,
  que no pide token y sigue respondiendo.
- **Lo que se rompe es la actualización de la demo**: fichas, tapas, cantidad de stock y listados.
- **Precios, editorial y "agotado desde" se pueden obtener igual** por el buscador web (es el mismo
  canal que usa la autoconsulta, un pedido por ISBN).

## Regla de trabajo (para no volver a mezclar)

Antes de decir "X depende de Y", en este proyecto se busca en el código y se cita **archivo:línea**.
Si no está verificado, no se afirma. La frase "depende de las APIs" sin esa comprobación no se usa
nunca más.

## Verificación del 04/11, 22:20 — todo lo que usa la autoconsulta funciona

| Componente | Prueba | Resultado |
|---|---|---|
| **Lector clientes/vendedores** | `POST /api/rayuela-consulta` con 3 ISBN | OK: autor, precio, colección, "agotado"; ISBN inexistente devuelve error claro |
| **Lector público (HTTPS)** | `https://lector.rayuelalaplata.com.ar/rayuela` | HTTP 200 y consulta con datos reales |
| **App de ferias** | `/salud` 200; usa el mismo `rayuela.consultar` que el lector | Operativa (no se probó el alta porque requiere usuario del local) |
| **Novedades (scraping)** | motores zivals / yenny / sbs con 4 ISBN | OK con datos: ALEPH (9789875666481) en los tres; AGUA SALADA en yenny y sbs (editorial Pequeño Editor) |
| **Demo** | portada, búsqueda, ficha, carrito, institucional | HTTP 200 con datos del 04/11 10:25 |
| Actualización REST (stock, fichas, tapas) | — | **Bloqueada por token** |

Conclusión: la librería no perdió ninguna función. Lo único bloqueado es la actualización de la demo.


## Autoconsulta: precios si, stock no

El endpoint de autoconsulta que usa el local es:

```
http://rayuela1.serveftp.net:9090/BSGestion/BuscadorProductosAction.do
  ?method=buscarArticulo&buscarPorDescripcion=false&id=<ISBN>
```

Devuelve id, titulo, precio, ISBN, descripcion y propiedades (AUTOR, TEMA1-3, etc.).
**No devuelve stock.** El unico dato de disponibilidad es `AGOTADO DESDE`, que no es
la cantidad.

Por lo tanto:

- **Precio**: se verifica contra la autoconsulta.
- **Stock**: viene de la API v1 (`/api/productos`, campo `stock`) y no se puede
  contrastar contra la autoconsulta.
- No usar `stockVenta` del webservice viejo como si fuera stock real.
