# Búsqueda de la tienda: cómo está implementada (06/11/2026)

## Índice

- Tabla `buscar_fts` (FTS5): columnas `codigo` (sin indexar), `descripcion`, `autor`, `marca`,
  `temas`, `detalle`. Tokenizador `unicode61 remove_diacritics 2`.
- Se construye con `indexar_busqueda.py` sobre `productos where publicable = 1` (428.674 filas,
  ~3 s). Incluye la sinopsis.
- Relevancia: `bm25(buscar_fts, 0, 10, 6, 2, 3, 1)` → título ×10, autor ×6, temas ×3, editorial ×2,
  sinopsis ×1.

## Orden de búsqueda (de más exacto a más amplio)

| Paso | Condición | Implementación |
|---|---|---|
| 1 | ISBN (8-14 dígitos) | `codigo = ?` + `ESENCIALES` |
| 2 | una palabra | prefijo `"palabra"*` |
| 3 | varias palabras | `NEAR(w1 w2 …, 12)` — tienen que estar cerca |
| 4 | pares | `NEAR(w1 w2, 15) OR NEAR(w2 w3, 15) …` |
| 5 | tema sugerido | solo si no hubo resultados: palabra completa en el tema y ≥10 títulos |
| 6 | palabra por palabra | aviso con un link por palabra |

- Palabras vacías (`STOPWORDS`): el, la, de, que, un, libro, etc. Máximo 8 palabras.
- Corrección de errores (`¿Quisiste decir…?`): `difflib` contra la tabla `palabras`, **solo al
  buscar**, no en el desplegable.
- Errores de tiempos verbales/plurales no resueltos (juegan ≠ jugar) — pendiente.

## Desplegable mientras se escribe (`/api/buscar`)

- Solo prefijos exactos de lo tipeado, sin corregir ni adivinar.
- Solo resultados que coinciden en `descripcion`, `autor`, `marca` o `temas` (no sinopsis).
- Máximo 8, con tapa primero.

## Página de resultados (`/buscar`)

- Busca también en sinopsis; cada tarjeta muestra `motivo`: el fragmento de sinopsis que coincide
  («Coincide en la sinopsis: …»).
- Si no hay resultados: aviso de "palabras juntas", links por palabra y temas sugeridos.
- Orden por relevancia real: `instr()` sobre la lista de rowids que devuelve el índice.

## Cobertura

- 36.273 publicables con sinopsis (6.203 con stock). Sin sinopsis no hay búsqueda por argumento.
- Temas sucios (TAPAS = tapas de Página 12, temas de 1 título) → por eso el mínimo de 10 títulos.

## Pendiente / a decidir con los vendedores

- Frases reales para calibrar distancia y palabras ignoradas (`Frases-de-clientes-para-probar.csv`).
- Lista blanca de temas.
- ¿Resultados aproximados o estrictos cuando la frase no se encuentra junta?
- ¿Priorizar stock en el orden?
- Lematización simple (juegan/jugar/juego) si aparecen casos.

Documento para el equipo: `Busqueda-como-funciona-y-que-necesitamos.docx` (en el repo de la demo).
