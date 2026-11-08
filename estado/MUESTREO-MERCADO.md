# Muestreo de mercado

**Desde:** 08/11/2026. **Acceso:** Catálogo → Mercado (requiere equipo).

## Qué hace

Lee una vez por día las URLs cargadas (máximo 5) y guarda hasta 30 libros por URL:
posición, título, autor, precio, ISBN y link. Cruza por ISBN (o por título cuando no hay
ISBN) contra el catálogo de Rayuela para mostrar si el libro está, cuánto stock hay y a
qué precio.

No modifica el catálogo, no publica nada y no copia sinopsis ni imágenes.

## URLs iniciales

1. Aleph — más vendidos
2. Cúspide — Top 100
3. SBS — más vendidos
4. Yenny — ranking de ventas
5. Aleph — novedades

Se pueden pausar, eliminar y agregar otras desde la pestaña. El tope es 5.

## Cuándo corre

Timer `rayuela-mercado.timer`: todos los días a las **04:00**.
Servicio: `rayuela-mercado.service` (oneshot).
Log: `journalctl -u rayuela-mercado.service`.

## Cómo se apaga

```bash
systemctl disable --now rayuela-mercado.timer
```

La pestaña queda, pero sin datos nuevos. Las tablas `mercado_fuentes` y
`mercado_muestras` se pueden vaciar sin afectar la tienda.

## Límites

- Sitios con bloqueo o cambio de diseño pueden devolver menos títulos; el sistema
  guarda lo que pudo leer y sigue con la próxima URL.
- El parser es genérico (JSON-LD y tarjetas) con un caso específico para Cúspide.
  Si una URL nueva no devuelve nada, se ajusta el parser para ese sitio.
- Los precios son los que muestra cada librería, sin normalizar descuentos.
