# Cliente de la API v1 — estado y mapeo de campos

**Actualizado:** 04/11/2026 22:15 · Basado en `bridge/API-v1-extraido.txt` (documentación oficial, septiembre 2026).

## Lo que ya está escrito y probado (sin usar la red)

| Archivo | Qué hace |
|---|---|
| `demo_tienda/bridge_v1.py` | Cliente completo: `productos()` paginado, `producto(codigo)`, validación de campos, manejo de 400/401/404/500, guardas de autorización y pausa, limitador de ritmo, iterador de catálogo |
| `demo_tienda/tests_bridge_v1.py` | 14 pruebas con respuestas simuladas (no toca la red) |

Resultado: **14/14 pruebas OK**. Las pruebas encontraron un bug real (el código no escapaba `/` en la
ruta) y quedó corregido.

## Mapeo: campos de la v1 → base de la demo

| v1 | Nuestra base | Nota |
|---|---|---|
| `codigo` | — | **Es un código interno alfanumérico (ej. `001.001.0001`), NO el ISBN** |
| `codigoBarras` | `productos.codigo` | **El ISBN/EAN que usamos. Hay que cruzar por acá** |
| `descripcion` | `descripcion` | Título |
| `detalle` | `detalle` (sinopsis) | Descripción ampliada |
| `precioVenta` | `precio` | Precio con IVA, el que se muestra |
| `stock` | `stock` | Cuesta **una consulta extra por producto** según la doc: pedirlo sólo cuando se necesita |
| `marca` | `marca` (editorial) | |
| `rubro` / `categoria` | `temas` | Clasificación; requiere revisión con la librería |
| `fechaUltimaActualizacion` | — | Útil para detectar cambios de precio |
| `alicuotaIva`, `precioCosto`, `markup` | — | **No se usan** (datos internos del negocio) |

## Lo que la v1 **no** documenta (a confirmar con Luis)

1. **Imagen / portada**: no hay campo de imagen en la documentación de la v1. Las tapas hoy salen de la
   v0 (`/articulo/{isbn}/imagen`), que está bloqueada. Pregunta: ¿la v1 expone portada?
2. **Filtro por fecha de modificación**: la única forma de recorrer el catálogo es paginar de 50 en 50
   (8.953 páginas para 447.607 productos). No hay "modificados desde X".
3. **URL y puerto reales**: la doc dice `https://[servidor]/BSGestion/api` sin especificar. El puerto
   9090 no tiene TLS; hay que confirmar 443 u otro.

## Dos estrategias posibles cuando llegue el token

| Estrategia | Pedidos | Ventaja | Riesgo |
|---|---|---|---|
| **A · Por producto** (`/productos/{codigoBarras}`) | 1 por libro (26.000 para los que tienen stock) | Barato por pedido, no pide `stock` en lote | Más pedidos totales |
| **B · Catálogo paginado** (`/productos?campos=...`) | ~9.000 para todo el catálogo (50/página) | Recorre todo, detecta altas y bajas | Páginas con más costo por registro |

La decisión depende de **medir el tiempo por página y por producto** con el token real, igual que se
hizo con la v0. No se elige por intuición.

## Prueba del token recibido (04/11, 22:20)

Se probo el token entregado contra todos los destinos posibles. Resultado:

| Destino | Con token | Sin token |
|---|---|---|
| `http://rayuela1.serveftp.net:9090/BSGestion/api/productos` | 401 **Token invalido** | 401 Token no provisto |
| `http://rayuela1.serveftp.net:9090/BSGestion/api` | 401 **Token invalido** | — |
| `http://rayuela1.serveftp.net:443/BSGestion/api/productos` | 401 **Token invalido** | 401 Token no provisto |
| `http://rayuela1.serveftp.net:9090/BSGestion/rest/webservice/articulo/{isbn}/stock` | 401 **Token invalido** | 401 Token no provisto |

Datos del entorno descubiertos en la prueba:

- El **puerto 443 no tiene TLS**: es HTTP plano con **Apache Tomcat 8.5.82** (responde la pagina
  por defecto de Tomcat en `/`). La documentacion dice `https://`, pero ahi no hay certificado.
- El **puerto 9090 tampoco tiene TLS** (`curl https` da "wrong version number").
- Las rutas de la v1 (`/BSGestion/api`) y de la v0 (`/BSGestion/rest/webservice`) **ahora comparten
  la misma autenticacion**: ambas responden con el formato de error de la v1.

**Conclusion:** el token no sirve para esta instalacion (no es un problema de URL ni de puerto: el
header llega y el servidor lo evalua, pero lo rechaza). Hay que confirmar con Bridge si es el token
asignado a Rayuela o a otro sistema/entorno, y si roto con la actualizacion del 04/11.

Total de pedidos de esta verificacion: 10, todos rechazados con 401.
