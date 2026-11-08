# Administración: una sola barra de pestañas

**Desde:** 08/11/2026.

## Problema

Antes: panel → catálogo → otra fila de pestañas (Listado / Calidad / Estado / Mercado).
Dos niveles para llegar a una pantalla, y el usuario no sabía dónde estaba parado.
Además, Mercado era una página infinita con cinco tablas seguidas.

## Diseño actual

Una única barra superior, siempre visible:

**Resumen · Catálogo · Calidad · Estado · Mercado · Consultas · Diseño**

- No hay pestañas dentro de pestañas.
- **Resumen** muestra el estado de la tienda y la actualización de datos.
- **Catálogo** es el listado operativo.
- **Calidad**, **Estado** y **Mercado** son pantallas propias, no pestañas escondidas.
- **Consultas** queda al mismo nivel.
- **Diseño** agrupa identidad, colores y datos de contacto: todo lo que cambia la apariencia.
- Cada pantalla tiene un solo `h1` y el nombre de la sección.

## Mercado

- Tarjetas de resumen: URLs activas, libros muestreados, listas con datos y última corrida.
- Una lista por vez, seleccionable con chips.
- 12 títulos por página, con Anterior / Siguiente.
- La administración de URLs está plegada en “Administrar URLs”, no ocupa la pantalla.
- El detalle del muestreo no se mezcla con la configuración.

## Regla

Si una pantalla nueva necesita una sub-pestaña, primero se evalúa si puede ser una
pestaña principal. La administración no debe anidar navegación.
