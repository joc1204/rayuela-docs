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
| Copia en Drive | carpeta `Rayuela/Respaldos/` | ⬜ subir a mano |

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

- **Hoy**: manual. El paquete se genera con `bash /usr/local/bin/respaldo-externo.sh` y después se
  sube a Drive a mano.
- **Pendiente**: automatizar (cron nocturno que genere el paquete y lo suba con rclone), y que Drive
  tenga al menos 2 generaciones.

## Rotación

La passphrase la generó el agente y se mostró una vez en el chat. Recomendación: cuando se suba el
paquete a Drive, generar una nueva passphrase, volver a cifrar y guardar la nueva en el gestor.
