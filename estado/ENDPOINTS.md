# Endpoints vigentes de Rayuela

**Actualizado:** 08/11/2026. Esta es la referencia única: si un script no usa uno de
estos dos endpoints, está mal.

## 1. Autoconsulta — precio y metadatos (no stock)

```
http://rayuela1.serveftp.net:9090/BSGestion/BuscadorProductosAction.do
    ?method=buscarArticulo&buscarPorDescripcion=false&id=<ISBN>
```

- Sin token.
- Devuelve: id interno, título, precio (texto `$35.600,00`), ISBN, descripción y
  propiedades: AUTOR, EDICIÓN, ILUSTRADOR, COLECCIÓN, TEMA1, TEMA2, TEMA3, etc.
- **No devuelve stock.** El único dato de disponibilidad es `AGOTADO DESDE`, que no
  es cantidad.
- Uso: verificar precio, título, autor, temas y sinopsis de un ISBN.
- Script: `rayuela-docs/infra/bin/comparar_bridge.py`.
- Consumidores actuales: `ferias/rayuela.py`, `enriquecer_buscador.py`,
  `actualizar_precios_buscador.py`.

## 2. API v1 del servidor de pruebas — stock y clasificación

```
http://brd.serveftp.net:10160/BSGestionRayuela/api/productos
    ?pagina=1&limite=200&campos=codigo,descripcion,categoria,rubro,stock,
     precioVenta,detalle,autor,marca,coleccion,estado
```

- Token: `/etc/rayuela/bridge.env` (`BRIDGE_TOKEN`), header `Authorization: Bearer`.
- Páginas de hasta 200 registros; el catálogo tiene 449.499.
- Devuelve: `codigo` (ISBN que usamos), descripción, categoría, rubro, **stock**,
  precioVenta, detalle, autor, marca, colección, estado.
- Uso: sincronización completa (`demo/sincronizar_api.py`) y stock.
- **La autoconsulta no sirve para validar este stock.** No hay otro endpoint que lo
  dé en tiempo real por ahora.

## 3. API v0 — retirada

`/rest/webservice/...` fue dada de baja. No se usa en ningún script activo.
Los scripts viejos están archivados en `demo_tienda/legacy_v0/` y no se ejecutan.

## Regla de publicación

`publicar.sh` corre `auditar_endpoints.py` antes de dar una publicación por buena.
Si aparece `/rest/webservice` en el código activo, la publicación se rechaza.
