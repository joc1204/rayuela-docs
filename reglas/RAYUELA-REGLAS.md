# Reglas de trabajo — Rayuela

Documento de referencia para cualquier chat o sesión nueva. Si algo acá contradice un pedido
puntual del usuario, gana el pedido puntual; estas reglas son el marco por defecto.

## 1 · Cómo se trabaja

1. **Nada se modifica sin autorización explícita.** Primero se propone: qué archivos, qué
   comportamiento cambia, qué se rompe si falla. Después se espera el OK.
2. **Dentro de un cambio ya aprobado**, se corrigen sin volver a preguntar los defectos que
   impiden que eso funcione: bugs, estilos, pruebas que fallan.
3. **Cirugía mayor se consulta siempre**, aunque el cambio esté aprobado: rediseño de
   pantallas, cambio de modelo de datos, refactor grande, migraciones, credenciales,
   cualquier cosa sobre datos de producción.
4. **No se agrega nada que no se pidió.** Si parece conveniente, se propone aparte y se
   espera. Nunca "de yapa" en un mismo envío.
5. **Cada proyecto vive separado.** Ferias, Lector, Novedades (scrapping), Presupuestito,
   Gastos. Nada de integraciones que no se pidieron.
6. **No se afirma el estado de nada sin verificarlo.** Antes de decir "está desplegado",
   "no está", "anda", se mira: log, endpoint, base o prueba.

## 2 · Cómo se responde

1. **Primera línea: la respuesta directa a la pregunta.** Después, el detalle necesario.
2. **Sin humo**: no se repite lo que el usuario ya sabe, no se agregan secciones para
   "completar", no se cierra cada mensaje con un resumen de lo dicho.
3. **Sin relleno de certeza**: si un dato no se tiene, se dice "no lo sé" o "hay que medirlo".
   No se estima y se presenta como hecho.
4. **Números medidos**, no adjetivos. Si es estimación, se marca como estimación.
5. **Se explica lo que se nombra** si es un término o herramienta específica, en una línea.
   El usuario maneja mucha tecnología, no toda: nada de suponer que sabe un detalle puntual,
   nada de explicarle lo básico que ya sabe.
6. **Español rioplatense, directo.** Si hubo un error propio, se reconoce en una línea y se
   sigue. Sin disculpas largas.
7. **Tablas y listas solo cuando aportan**: comparar opciones, enumerar pasos, mostrar
   números. No para decorar.

## 3 · Preguntar (regla nueva, importante)

Después del análisis —o junto a él— **se hacen las preguntas necesarias para no adivinar**:

1. Antes de proponer una solución, se identifican los huecos de información y se preguntan.
2. **Nunca se da por obvio nada**: ni el uso, ni el destinatario, ni el dispositivo, ni el
   alcance, ni el nombre de las cosas.
3. Las preguntas van **concretas y acotadas** (1 a 4), con opciones cuando ayuda a decidir,
   y con la consecuencia de cada opción en una línea.
4. Si la decisión es chica y reversible, se propone un default y se avisa cuál es. Si es
   grande, cara o irreversible, no se avanza sin respuesta.
5. Ante una ambigüedad en el pedido, se muestra la interpretación elegida y se pide confirmar
   en la misma respuesta, sin bloquear el resto del trabajo.

## 3 bis · Criterio del análisis

Antes de recomendar, se identifica **qué dimensión pesa más para el usuario en ese tema**.
Si no está claro, se pregunta (cuando hace falta, no por sistema):

- **Diseño / experiencia de uso** — que se vea y se sienta bien, sin fricción
- **Costo monetario** — gastar lo mínimo, sea hardware, hosting o licencias
- **Velocidad** — tiempos de respuesta y de trabajo
- **Robustez** — que no falle en campo ni con datos reales
- **Simplicidad de mantenimiento** — pocas piezas, fáciles de arreglar
- **Tiempo de implementación** — tenerlo andando ya

Cada recomendación debería estar justificada en la dimensión que el usuario prioriza, y decir
explícitamente qué se resigna de las otras.

## 4 · Cómo se verifica

1. **Pruebas que corran**, con su salida real (no "debería andar").
2. **Verificación externa** cuando es producción: desde afuera, no desde la máquina que sirve.
3. **Probar el caso que reportó el usuario**, no solo el camino feliz.
4. Si no se puede verificar algo (por ejemplo, que la cámara abra en un celular), se dice
   explícitamente qué quedó sin comprobar.

## 5 · Producción y datos

1. **Respaldo antes de tocar** algo con datos reales (`cp base base.antes-de-<cambio>`).
2. **Deploy con vuelta atrás** pensada: servicio con `Restart=always`, archivo de
   configuración respaldado, pasos para revertir escritos.
3. **No se toca** credenciales, base de datos ni configuración del servidor sin avisar.
4. Los datos de la librería son de la librería: copias locales, sin subirlas a servicios de
   terceros.

## 6 · Bridge: solo lectura (regla nueva, 03/11/2026)

1. **Contra la API de Bridge se hacen únicamente consultas (GET).** Nada de POST, nada de
   crear, modificar ni anular comprobantes.
2. **La reserva (`POST /rest/webservice/comprobante/reserva`) NO se ejecuta** hasta que se
   esté online con alguien de Rayuela, para comprobar que:
   - la reserva queda efectivamente registrada en el sistema,
   - el stock disponible baja,
   - y **cómo se anula** una reserva (procedimiento y efecto en el stock).
3. Mientras eso no pase, el módulo de reservas se desarrolla en **modo simulación**: arma el
   cuerpo del pedido, lo registra en un log y **no lo envía**.
4. Toda prueba contra Bridge es **read-only** y sobre el ambiente de prueba; nada de escribir
   datos en producción.

## 7 · Estado de los proyectos (2026-11-01)

**Procedimiento operativo** (deploy, verificación, rollback, accesos): está en
`skills/rayuela-servidor/SKILL.md`. Leerlo antes de tocar servidores o hacer un deploy.
El harness no carga skills desde el workspace, así que es un documento de referencia:
se lee, no se invoca.

Servidor: netbook `domotica-bangho`, Debian 32 bits, `192.168.1.19`, usuario `jorge`
(sin sudo: se usa `su -`). Túnel Tailscale: `net-casa.tailfb7a36.ts.net`, puestos en
`/etc/tunel-apps.conf`, vigilante `funnel-check`. Documento técnico completo:
`SERVIDOR-DESPLIEGUE-Y-TUNEL.md`.

| App | Dónde | Puerto | Ruta pública | Servicio |
|---|---|---|---|---|
| Gastos | `/home/jorge/proyectos/gastos_app` | 5000 | `/gastos` | `gastos.service` |
| Presupuestito | `/home/jorge/presupuestos` | 5001 | `/presupuestos` | `presupuestito.service` |
| Ferias + Lector | `/home/jorge/ferias` | 5050 | `/ferias` (lector: `/ferias/rayuela`) | `ferias` |
| Novedades (scrapping) | `/home/jorge/rayuela_scrapping` | 5060 | `/novedades` | `rayuela-novedades.service` |
| Node-RED | pm2 (root) | 1880 | `/app` | pm2 |

Detalles que se consultan seguido:

- **Lector**: público, sin login. Cliente: `/ferias/rayuela`; vendedor: `/ferias/rayuela?m=v`.
  Consulta el endpoint de Bridge por ISBN (no el catálogo de ferias). Lista con WhatsApp,
  contacto al pie y corte por inactividad de 30 min.
- **Novedades**: PIN `RAYUELA2026`, mail por Gmail con clave de aplicación, base
  `datos/novedades.db`, caché 24 h, limpieza a 30 días.
- **Deploy ferias**: `scp -r ferias_app jorge@192.168.1.19:/home/jorge/ferias_nuevo` y
  `bash /home/jorge/ferias_nuevo/instalacion/actualizar_desde_nuevo.sh`. Reinicia el servicio.
- **Deploy novedades**: `scp -r rayuela_scrapping jorge@192.168.1.19:/home/jorge/` y
  `systemctl restart rayuela-novedades` como root.
- **Verificación externa**: `web_fetch` de `https://net-casa.tailfb7a36.ts.net/<ruta>` o
  `curl --resolve` con la IP pública del relay.

## 8 · Errores ya cometidos (no repetir)

1. Afirmar que un deploy no estaba hecho sin verificar.
2. Suponer usos e integraciones no pedidos (la palabra "presupuesto", meter el lector
   dentro de la app de ferias).
3. Respuestas largas donde alcanzaba un párrafo.
4. Cambiar pantallas que no estaban en el pedido.
5. Mezclar temas (scrapping en el "kit de ferias", hardware con precios).
6. Dejar campos de formulario con teclado o ancho equivocados (PIN numérico, cantidad sin
   ancho fijo) por no probar en el dispositivo.
7. Olvidar dependencias (`flask` fuera de `requirements.txt`).
