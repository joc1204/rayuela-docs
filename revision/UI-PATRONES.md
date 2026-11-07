# Patrones de interfaz del panel

Reglas para que una pantalla quede bien desde la primera vez. Se aplican antes de
publicar cualquier cambio de interfaz.

## Verificación obligatoria antes de mostrar

1. Generar el HTML de la pantalla (sin las barras, para ver el contenido):

       CATALOGO_DB=/opt/rayuela/demo/catalogo.db DEMO_CLAVE=... RAYUELA_BASE=/opt/rayuela/demo \
       /opt/rayuela/ferias/venv/bin/python /opt/rayuela/capturas/vista_previa.py \
         --ruta /admin/catalogo --salida /tmp/pantalla.html --sin-barras

2. Sacar capturas en tres anchos:

       /opt/rayuela/capturas/venv/bin/python /opt/rayuela/capturas/capturar_ui.py \
         --html /tmp/pantalla.html --salida /tmp/capturas --nombre catalogo \
         --anchos 1280,1024,390

3. Mirar las tres capturas y compararlas contra este documento. Si algo no cumple,
   se corrige antes de publicar. **Nunca se le pide a Jorge que descubra esto.**

## Controles

| Control | Alto | Letra | Padding | Radio |
|---|---|---|---|---|
| input / select | 34 px | 13,5 px | 0 9 px | 7 px |
| botón principal | 36 px | 14,5 px | 8 px 20 px | 8 px |
| botón chico | 30 px | 13 px | 5 px 10 px | 6 px |

- Etiquetas de campo: 10,5 px, mayúsculas, `letter-spacing: .05em`, color tenue,
  4 px de separación con el control.
- Títulos de bloque: 10,5 px, mayúsculas, peso 650, 7 px antes del primer campo.

## Formularios de filtros

- Agrupar por concepto y titular cada bloque. Nunca una fila única que se acomoda sola.
- Grilla fija por fila (`grid-template-columns`), filas que llenan el ancho de la tarjeta.
- Un solo botón primario por pantalla ("Filtrar"), al final de su bloque.
- Las acciones que guardan algo ("Guardar vista") van separadas por una línea
  punteada, con su propio campo de nombre.
- La tarjeta de filtros debe terminar a la misma altura que las tarjetas de abajo.

## Prohibido

- Dejar que una regla general (`.panel label input { width:100% }`) pise los anchos
  específicos: usar selectores con la misma especificidad o mayor (`.form-filtros ...`).
- Campos de texto más anchos que 320 px sin motivo.
- Botones gigantes al lado de campos chicos.
- Etiquetas que digan "Ver" cuando el resto dice "Estado".
- Mostrar la palabra "ficha" u otro término interno en pantalla.

## Capturas

Las capturas revisadas se guardan en `revision/capturas/` con fecha y ancho:
`2026-11-07-catalogo-1280.png`, `-1024.png`, `-390.png`.
