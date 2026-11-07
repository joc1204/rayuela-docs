# Revisión UX/UI de las pantallas

Se aplica **antes de publicar** cualquier cambio de interfaz. Dos capas: chequeos automáticos
(en `auditar_ui.py`) y una revisión independiente contra esta lista.

## Reglas duras (las verifica el auditor)

1. **Navegación arriba**: en toda pantalla del panel, el acceso a la tienda y la vuelta al panel
   están arriba, visibles sin scrollear.
2. **Acciones antes que el listado**: si una pantalla muestra una tabla larga (más de 50 filas),
   las acciones sobre esa lista (ocultar, mostrar, aplicar al total) van **arriba de la tabla**,
   y la barra queda fija al scrollear.
3. **El estado se muestra**: si hay un criterio de filtro aplicado, tiene que verse escrito en
   pantalla, con opción de quitarlo.
4. **Ningún control muerto**: todo botón o link hace algo. Textos tipo "ver más…" sin acción
   no se permiten.
5. **Un nombre por concepto** y un solo `<h1>` por pantalla.
6. **Celular primero**: la pantalla tiene que poder usarse a 360 px de ancho sin scroll
   horizontal para las acciones principales.
7. **Destructivo protegido**: ocultar/aplicar a todo confirma con el número exacto afectado.

## Preguntas para el revisor independiente

- ¿Se entiende de un vistazo qué hace la pantalla, sin leer instrucciones?
- ¿Hay que scrollear para encontrar la acción principal? (si sí: defecto)
- ¿Algún control parece hacer algo y no hace nada? ¿Algún texto promete algo que no ocurre?
- ¿El flujo se puede completar en el celular a una mano?
- ¿Los números en pantalla coinciden con lo que dice la base?
- ¿Hay pasos que se pueden ahorrar? (selección página por página, doble confirmación inútil)
- ¿Un texto nuevo usa el mismo nombre que ya usa la pantalla para ese concepto?

## Cómo se registra

- Informe en `_revision/AAAA-MM-DD-ux.md` y copia en `rayuela-docs/revision/`.
- Cada defecto: severidad (crítico / importante / menor), pantalla, qué pasa, qué se espera.
- No se publica con defectos críticos abiertos; los importantes se corrigen o se anotan.
