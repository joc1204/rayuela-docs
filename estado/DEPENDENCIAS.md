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
