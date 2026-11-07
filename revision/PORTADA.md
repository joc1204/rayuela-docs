# Cómo se arma la portada y cómo se revisa

Registro vivo. Última revisión: 07/11/2026, 01:50.

## Composición actual

En este orden:

1. **Destacados**: los títulos marcados por el librero, en la tabla `destacados`, hasta 12.
2. Si no hay destacados: **12 títulos al azar** que tengan tapa y stock.
3. **Lo más visto esta semana**: títulos abiertos en los últimos 7 días (eventos).
4. **Lo que más se busca**: términos buscados, con la cantidad.
5. **Recomendados de la visita**: según lo que miró el visitante.

Código: `demo_tienda/app.py` — `destacados()` línea 600, portada línea 628,
estadísticas de portada en `estadisticas_portada()`.

## Dónde se elige qué va en la portada

**Catálogo → columna "Portada"** de cada fila:

- `Destacar`: agrega el título a la portada.
- `Quitar de portada`: lo saca.

Y al final de esa misma pantalla, la sección **"Destacados en la portada"** lista los
elegidos con su botón de quitar. Si no hay ninguno, ahora lo dice explícitamente:
"Todavía no hay destacados. Mientras no haya, la portada muestra 12 títulos al azar
con tapa y stock."

## Estado al 07/11/2026

| Dato | Valor |
|---|---|
| Títulos destacados | **0** |
| Títulos en el catálogo | 428.674 |
| Disponibles hoy (stock > 0) | 25.731 |
| Portada | 12 al azar con tapa y stock |

## Revisión visual

Capturas del 07/11: `revision/capturas/2026-11-07-portada-1280.png`,
`-1024.png` y `-390.png` (sacadas por HTTPS, con las tapas cargadas).

Lo que se ve:

- La primera franja muestra 12 títulos, 6 por fila en escritorio y 2 en celular.
- "Lo más visto" trae 11 títulos: la última fila queda despareja (6 + 5).
- "Lo que más se busca" incluye ISBN sueltos (9788493464110, 9780230010086).
- Hay precios dudosos visibles en la portada: $ 1 (Agenda 2019), $ 195, $ 295, $ 530.
- Hay títulos repetidos por edición (dos "Pachorra").

## Pendientes que salen de esta revisión

- Decidir si se curan destacados para la demo (Hoy son 0).
- Definir un precio mínimo publicable (los $ 1/$ 195 son datos de Rayuela, no de la web).
- Emparejar las franjas: 12 y 12, no 12 y 11.
- Ver si conviene un enlace "Ver todo" al final de cada franja.
- Revisar que "Lo que más se busca" no muestre ISBN sueltos.
