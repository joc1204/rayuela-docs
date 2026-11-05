# Política de carga sobre el servidor de Rayuela (Bridge)

**Regla madre:** el servidor es de la librería; nosotros somos invitados. Cualquier duda, se consulta
antes de ejecutar.

## Ventana

| Franja | Permitido |
|---|---|
| **21:00 a 08:00** | trabajos de actualización (con autorización de Jorge) |
| **08:00 a 21:00** | **nada automático**. Sólo el endpoint de autoconsulta que dispara una persona |
| Viernes con evento | **nada** (ver `PROYECTO-ESTADO.md`) |

## Presupuesto por tipo de pedido

| Endpoint | Costo medido | Regla |
|---|---|---|
| `articulo/{isbn}/stock`, `/precio`, `/imagen` | 0,05 s | permitido, uno por libro |
| `articulos/precio/{fecha}/{pag}` | 0,05 s por página de 100 | permitido para detectar cambios |
| `articulo/{isbn}` (ficha completa) | 1,6 s | sólo de noche, en tandas chicas |
| `articulos/stock/{fecha}/{pag}` | 9,3 s por página | **prohibido** salvo autorización explícita |
| `articulos/atributos/{fecha}/{pag}` | 9,7 s (pág. 1) hasta 30 s (pág. 4.000+) | **prohibido** (barrido desde 1900 ya está hecho) |
| `BuscadorProductosAction.do` (autoconsulta) | 1 pedido por ISBN | permitido; a ritmo bajo también en lote |

## Ritmo

- **Máximo absoluto: 3 pedidos por segundo** compartidos entre todos los procesos
  (`/var/lock/rayuela-bridge-ritmo`).
- **Un solo proceso a la vez** contra Bridge (`/run/rayuela-bridge.lock`).
- Objetivo de trabajo: **1,5 a 2 pedidos/s**. Subir a 3 sólo si la medición de latencia del punto
  siguiente da bien.
- **Nunca más de un hilo por cada 2 pedidos/s**: para acelerar se amplía la ventana, no el paralelismo.

## Medición obligatoria (antes, durante y después)

1. **Antes**: `python3 /opt/rayuela/demo/verificar_hechos.py` → autorización, pausa, cero conexiones.
2. **Línea de base**: un pedido a `articulo/{isbn}/stock`, anotar el tiempo.
3. **Cada 15 minutos** durante el trabajo: repetir ese pedido.
   - Si tarda **más del doble** que la línea de base → bajar el ritmo a la mitad.
   - Si tarda **más de 3 segundos** → **cortar** y avisar.
4. **Al terminar**: registrar ritmo promedio, pedidos totales, latencia inicial y final.

## Prohibiciones

- Escrituras de cualquier tipo (la API es de lectura).
- Barridos de catálogo completo por listados paginados.
- Cualquier consulta sin autorización escrita de Jorge (`/etc/rayuela/autorizacion-bridge`).
- Ejecutar dos trabajos simultáneos.
- "Probar si aguanta": no se sube el ritmo sin medir.

## Registro de incidentes

| Fecha | Qué pasó | Ritmo | Consecuencia |
|---|---|---|---|
| 03/11 18:58-19:40 | tapas con 9 hilos + stock + metadatos en horario de cierre | 50-60 pedidos/s | cierre de caja lento; soporte activado |
| 04/11 10:36 | corte total preventivo | 0 | se detuvo todo y se implementó la doble llave |

## Si Bridge cambia algo (token, endpoints)

1. **No improvisar**: no se prueban variantes a mano.
2. Se lee la documentación (`bridge/`) y se verifica con **un** pedido controlado.
3. Si hay bloqueo, se avisa a Jorge y se deja todo detenido. El token va en
   `/etc/rayuela/bridge.env` (640 root:rayuela), nunca en el proyecto.
