# Registro de proyectos — Rayuela

**Actualizado:** 05/11/2026 08:55 · Fuente: código desplegado en el VPS, no memoria.
Cada dato tiene su archivo:línea o su comando de verificación.

## Reglas de convivencia entre proyectos

1. **Cada proyecto tiene su carpeta y su servicio.** Un agente sólo escribe en las carpetas del
   proyecto que tiene asignado. Fuera de eso, no toca.
2. **Código compartido se trata como "cruzado"**: un cambio ahí obliga a correr las pruebas de
   *todos* los consumidores, no sólo del proyecto donde se hizo.
3. **Una funcionalidad no se mueve de proyecto** sin una tarea que lo declare y sin actualizar este
   archivo.
4. **Nada de copias**: si dos proyectos necesitan lo mismo, se comparte la biblioteca o se duplica
   con dueño y aviso. Hoy hay una copia del scraper que hay que unificar (ver pendientes).

## Fichas

### Ferias
- **Código:** `/opt/rayuela/ferias` · **Puerto:** 5050 · **Servicio:** `ferias`
- **Para qué:** venta en ferias escolares, carga de libros, caja y consulta de ISBN.
- **Usa:** `rayuela.consultar` → `BuscadorProductosAction.do` (autoconsulta, sin token).
- **Usado por:** el Lector (mismo código).
- **No debe:** tocar la demo ni Novedades.

### Lector (vendedores y clientes)
- **Código:** el mismo de Ferias (rutas `/rayuela` y `/api/rayuela-consulta`).
- **Para qué:** autoconsulta de precio y disponibilidad por ISBN.
- **Usa:** la misma `rayuela.consultar`.
- **Nota:** no es un proyecto separado: es una ruta dentro de la app de ferias. Cualquier cambio en
  `rayuela.py` afecta a Ferias, Lector y al scraper del Novedades.

### Prueba
- **Código:** `/opt/rayuela/prueba` · **Puerto:** 5051 · **Servicio:** `ferias-prueba`
- **Para qué:** ambiente de prueba de la app de ferias.
- **No debe:** usarse para nada de producción.

### Demo de tienda
- **Código:** `/opt/rayuela/demo` (repo `rayuela-demo`) · **Puerto:** 5052 · **Servicio:** `rayuela-demo`
- **Para qué:** tienda online de demostración con el catálogo real.
- **Usa:** API REST v0 (`/rest/webservice/...`) para fichas, stock, tapas y metadatos.
- **Bloqueo actual:** Bridge exige token y el token disponible da 401 (ver `API-V1-CLIENTE.md`).
- **Publicación:** sólo a través de `publicar.sh` (puerta de humo obligatoria).

### Novedades (scraping)
- **Código:** `/opt/rayuela/novedades` (repo `rayuela_scrapping`) · **Puerto:** 5060 · **Servicio:** `rayuela-novedades`
- **Para qué:** buscar ISBN en librerías de terceros (zivals, yenny, sbs) y avisar por mail.
- **Usa:** `sitios.py` (motores de scraping).
- **No debe:** consultar Bridge.

### Tapas externas (cubre-faltantes de la demo)
- **Código:** `demo/tapas_externas.py` · corre como trabajo de sistema en el VPS.
- **Para qué:** completar tapas de libros que Bridge no tiene.
- **Usa:** **una copia** de los motores de scraping de Novedades.
- **Riesgo:** la copia puede quedar desactualizada. Pendiente: unificar.

## Matriz de dependencias cruzadas

| Pieza compartida | La usan | Si se cambia, hay que probar |
|---|---|---|
| `rayuela.consultar` (BuscadorProductos) | Ferias, Lector | la app de ferias y el lector |
| `sitios.py` (motores de scraping) | Novedades | Novedades y tapas externas (hoy con copia) |
| Base `catalogo.db` | Demo | humo de la demo |
| Telegram (`/usr/local/bin/avisar`) | Demo, salud, respaldo | los tres |

## Dueños (cuando se trabaja con agentes)

| Agente | Escribe en | No escribe en |
|---|---|---|
| Demo | `demo_tienda/`, `/opt/rayuela/demo`, repo `rayuela-demo` | ferias, lector, novedades |
| Ferias + Lector | `/opt/rayuela/ferias`, `/opt/rayuela/prueba` | demo, novedades |
| Novedades + Scraping | `/opt/rayuela/novedades`, `rayuela_scrapping/` | demo, ferias |
| QA | `tests/`, `humo.py`, documentación de pruebas | código de producto |
| Lead | `rayuela-docs/`, `publicar.sh`, despliegue | código de producto |

## Verificación

```bash
# estado general (no toca Bridge)
python3 /opt/rayuela/demo/verificar_hechos.py

# puerta de publicación de la demo (reinicia, mide y revierte si falla)
bash /opt/rayuela/demo/publicar.sh
```
