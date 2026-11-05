# Secretos del VPS — inventario y recuperación

**Regla:** los valores **no** se guardan en este repositorio ni en documentos. Viven en
`/etc/rayuela/*.env` en el VPS (permisos 600/640) y en el **gestor de contraseñas de Jorge**.
Este documento dice qué existe, para qué sirve y cómo se regenera.

## Inventario

| Secreto | Archivo en el VPS | Para qué | Cómo se regenera |
|---|---|---|---|
| `BRIDGE_TOKEN` | `/etc/rayuela/bridge.env` | API de Bridge (v0/v1) | lo entrega Bridge (Luis). El actual da 401 |
| `TELEGRAM_TOKEN` | `/etc/rayuela/telegram.env` | bot `@RayuelaRepoBot_bot` | con `/revoke` en @BotFather |
| `TELEGRAM_CHAT` | ídem | chat que recibe los avisos | se obtiene con `getUpdates` |
| `DEMO_CLAVE` | `/etc/rayuela/demo.env` | clave del panel de la demo (`/admin`) | se elige y se escribe ahí |
| `ALERTA_*` (host, puerto, usuario, clave, remitente, destino) | `/etc/rayuela/alerta.env` | avisos por mail desde el servidor | cuenta de correo del proveedor |
| `NOVEDADES_SMTP_*` + `NOVEDADES_MAIL` | `/etc/rayuela/novedades.env` | enviar el informe de Novedades | clave de aplicación de Gmail |
| `NOVEDADES_PIN` | ídem | PIN de acceso al panel de Novedades | se elige |
| Claves SSH de GitHub (`github_rayuela`, `github_rayuela_docs`, …) | `/root/.ssh/` | empujar repos a GitHub | se regeneran y se vuelven a cargar como deploy keys |
| Clave SSH del VPS (`ferias_ed25519`) | en la PC de Jorge | entrar al VPS | se regenera desde el panel de DonWeb (consola) |
| Acceso a Cloudflare / DNS del dominio | cuenta de Jorge | subdominios y certificados | proveedor |
| Token OAuth de Google Drive (rclone) | `/root/.config/rclone/rclone.conf` (600) | subir el respaldo cifrado | se revoca desde la cuenta de Google y se vuelve a autorizar |
| Acceso al panel de DonWeb | cuenta de Jorge | recrear el VPS | proveedor |

## Cómo se guardan hoy (verificado el 05/11)

- `/etc/rayuela/*.env`: permisos 600 (raíz) y 640 donde el servicio necesita leer.
- **No están incluidos** en el respaldo automático (`/var/backups/rayuela/config-*.tar.gz` sólo
  lleva nginx, unidades, sshd y letsencrypt). Decisión correcta: un `.tar.gz` plano con tokens sería
  un riesgo.
- Consecuencia: **si se pierde el VPS, los secretos se pierden** y hay que regenerarlos uno por uno.

## Procedimiento recomendado (pendiente de hacer)

1. Cargar cada valor en el gestor de contraseñas (Bitwarden o KeePass) en una entrada
   "Rayuela — VPS".
2. Guardar el archivo del gestor con su clave maestra, fuera de las máquinas del proyecto.
3. Rotación: si se sospecha exposición, se regenera el token en el proveedor y se actualiza el
   `.env`; no se toca el código.
4. Cuando se haga el respaldo externo (punto B), los `.env` van en un archivo **cifrado** aparte,
   nunca en el tar de configuración.

## Si hay que rotar el token de Bridge

1. Pedir el nuevo a Bridge.
2. Escribirlo en `/etc/rayuela/bridge.env` (sin dejarlo en el historial de la shell).
3. `chmod 640`, dueño `root:rayuela`.
4. Verificar con `python3 /opt/rayuela/demo/verificar_hechos.py` que lo detecta.
5. Probar **un** pedido autorizado antes de cualquier trabajo.
