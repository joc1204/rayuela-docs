# Respaldo externo (cifrado)

**Generado:** 05/11/2026 10:30 · **Script:** `infra/bin/respaldo-externo.sh`

## Qué contiene el paquete

| Pieza | Tamaño en el paquete | Por qué |
|---|---|---|
| `catalogo.db` | ~53 MB | los 447.607 títulos con precio y stock: **lo único que hoy no se puede volver a bajar** |
| `fichas/` | ~6 MB comprimidas (66.957 archivos) | sinopsis, editorial y páginas ya descargadas |
| `config.tar.gz` | 13 KB | unidades systemd, nginx, scripts del servidor |

**No incluye**: tapas (1,45 GB, se pueden re-scrapear), secretos (`/etc/rayuela/*.env`) ni bases de
ferias (chicas, ya respaldadas aparte).

## Dónde está

| Copia | Ubicación | Estado |
|---|---|---|
| Original en el VPS | `/var/backups/rayuela/externo/rayuela-2026-11-05.tar.gz.gpg` | ✅ |
| Copia en la PC | `default-workspace/_respaldos/rayuela-2026-11-05.tar.gz.gpg` | ✅ |
| Copia en Drive | cuenta **joc1204.developer@gmail.com** → carpeta **`Rayuela-respaldo`** | ✅ automática desde el 05/11 |

Integridad del archivo del 05/11:

```
tamaño:  58 MB
sha256:  a910e5fa3b0d2344a62e60db7aea85e4e263d61d78988099994005ffa98c3d6a
```

## La passphrase

El paquete está cifrado con **AES-256** (gpg simétrico). La passphrase **no está en este
repositorio**: se guardó en el VPS (`/root/.respaldo-pass`, 600) y debe guardarse en el gestor de
contraseñas de Jorge (entrada: *Rayuela — respaldo externo*).

Sin esa passphrase, el archivo es ilegible. Esa es la idea.

## Cómo se restaura

```bash
# 1. descargar el paquete
# 2. descifrar (pide la passphrase)
gpg --decrypt rayuela-2026-11-05.tar.gz.gpg > paquete.tar.gz

# 3. ver contenido antes de pisar nada
tar tzf paquete.tar.gz | head

# 4. extraer
mkdir restaurado && tar xzf paquete.tar.gz -C restaurado

# 5. reponer
#    restaurado/catalogo.db      -> /opt/rayuela/demo/catalogo.db
#    restaurado/fichas/          -> /opt/rayuela/demo/fichas/
#    restaurado/config.tar.gz    -> extraer en /  (unidades, nginx)
# 6. reindexar la búsqueda y verificar
#    python /opt/rayuela/demo/indexar_busqueda.py
#    python /opt/rayuela/demo/indexar_palabras.py
#    bash /opt/rayuela/demo/publicar.sh
```

## Cadencia

- **Automático**: `respaldo-nube.timer` corre todos los días a las **03:40** (con hasta 10 min de
  dispersión). Genera el paquete cifrado y lo sube a `drive:Rayuela-respaldo`. Mantiene las últimas
  **3 generaciones** en Drive y **5** en el VPS.
- **Manual, cuando se quiera**: `bash /usr/local/bin/subir-respaldo-drive.sh`.
- Log: `/var/backups/rayuela/externo/respaldo-nube.log`.
- **Regla**: la cuenta de Drive no se comparte. La passphrase va en el gestor de contraseñas, con la
  ubicación anotada al lado.

## Rotación

La passphrase la generó el agente y se mostró una vez en el chat. Recomendación: rotarla cuando se
pueda (generar una nueva, volver a cifrar y actualizar el gestor).

## Acceso a Drive desde el VPS

El VPS usa **rclone** con un token OAuth de la cuenta `joc1204.developer@gmail.com`
(`/root/.config/rclone/rclone.conf`, permisos 600). El token permite crear y borrar archivos en el
marco de esa cuenta. Para revocarlo: cuenta de Google → Seguridad → Aplicaciones de terceros →
quitar el acceso de "rclone". Después hay que volver a autorizar.

El **sha256 cambia cada vez** que se regenera el paquete (gpg agrega sal), así que no conviene
anotarlo como dato fijo: sirve sólo para verificar una copia puntual.
