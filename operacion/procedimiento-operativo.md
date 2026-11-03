---
name: rayuela-servidor
description: Cómo desplegar, verificar y revertir las apps de Rayuela (ferias + lector en el VPS, novedades, gastos y presupuestito en la netbook). Cargar antes de tocar servidores, hacer un deploy o diagnosticar una caída.
---

# Servidor de Rayuela: desplegar, verificar, revertir

Todo lo de acá está verificado en producción. Si algo no coincide, gana la realidad: revisar y actualizar.

## Dónde corre cada cosa

| App | Dónde | Servicio | URL |
|---|---|---|---|
| Ferias + Lector | **VPS** `201.32.132.197` (DonWeb, Argentina) | `ferias.service` (user `rayuela`, `/opt/rayuela/ferias`) | `https://ferias.rayuelalibros.com.ar` (temporal: `https://201.32.132.197.sslip.io`) |
| Novedades (scrapping) | netbook `192.168.1.19` | `rayuela-novedades.service` (puerto 5060) | `https://net-casa.tailfb7a36.ts.net/novedades` |
| Gastos | netbook | `gastos.service` (5000) | `/gastos` por el túnel |
| Presupuestito | netbook | `presupuestito.service` (5001) | `/presupuestos` por el túnel |

- **VPS**: Ubuntu 24.04, 2 vCPU / 2 GB / 14 GB, nginx + certbot, ufw (5186, 80, 443), fail2ban (`sshd`, `nginx-rayuela-limit`).
- **Netbook**: Debian 32 bits, usuario `jorge` **sin sudo** (usar `su -`), túnel Tailscale con puestos en `/etc/tunel-apps.conf`.
- La app de ferias **ya no corre en la netbook**: se frenó y se deshabilitó cuando migró al VPS.

## Accesos

- SSH al VPS: `ssh -i .ssh_keys/ferias_ed25519 -p 5186 root@201.32.132.197` (solo clave; la contraseña de root no entra por SSH).
- SSH a la netbook: `ssh -i .ssh_keys/id_rsa jorge@192.168.1.19`.
- Claves en `.ssh_keys/` del workspace. **Nunca** versionarlas.
- Secretos del plotter: `/home/jorge/rayuela_scrapping/servicio/.env` en la netbook (mail, PIN).

## Deploy de ferias (VPS)

1. Antes: pruebas locales `python tests_flujo.py` → tiene que decir `TODO OK`.
2. Copiar solo lo que cambió, o todo el código sin el venv:
   `scp -i .ssh_keys/ferias_ed25519 -P 5186 -r <archivos> root@201.32.132.197:/opt/rayuela/ferias/`
3. Ajustar dueño y reiniciar:
   `ssh ... 'chown -R rayuela:rayuela /opt/rayuela/ferias && systemctl restart ferias'`
4. Verificar desde afuera (no desde el servidor): `web_fetch https://ferias.rayuelalibros.com.ar/salud` → `{"app":"ferias","ok":true}`.
5. Si tocaste HTML/JS estático, subir el `?v=` de `base.html`/`lector.html` para que los celulares tomen el archivo nuevo.

Los archivos de datos (`ferias.db`) **no** se copian en un deploy normal.

## Deploy de novedades (netbook)

1. Pruebas: `python tests/test_sitios.py`, `tests/test_isbn.py`, `tests/test_web.py` → `TODO OK`.
2. `scp -r rayuela_scrapping jorge@192.168.1.19:/home/jorge/`
3. Como root: `systemctl restart rayuela-novedades`.
4. Verificar: `curl -s 127.0.0.1:5060/salud` y un trabajo de prueba por consola.

## Respaldos

- Ferias (VPS): copia diaria de `ferias.db` comprimida (revisar que exista y tenga fecha de hoy).
- Antes de cualquier cambio de datos: `cp ferias.db ferias.db.antes-de-<algo>`.
- La base de la netbook vieja quedó sincronizada con el VPS; sirve como respaldo de rollback.

## Rollback

- **Ferias al servidor anterior (netbook)**: como root `systemctl enable --now ferias`. La netbook tiene la misma base y claves.
- **Ferias en el VPS, código anterior**: `git log` en el workspace, volver al commit, copiar y reiniciar.
- **Certificado/DNS**: si el dominio falla, el nombre temporal `https://201.32.132.197.sslip.io` sigue sirviendo.

## Verificación rápida (una pasada)

```bash
# en el VPS
systemctl is-active ferias nginx fail2ban
curl -s -o /dev/null -w '%{http_code}\n' https://ferias.rayuelalibros.com.ar/ingresar
curl -s https://ferias.rayuelalibros.com.ar/salud
df -h / | tail -1

# desde afuera
web_fetch https://ferias.rayuelalibros.com.ar/salud
```

## Reglas que no se rompen

1. Nada de cambios sin autorización; propuesta primero (archivos + comportamiento).
2. Respaldo antes de tocar datos de producción.
3. Verificar **desde afuera**, nunca desde la máquina que sirve.
4. No copiar bases ni `secreto.key` a la web ni a repositorios.
5. Producción de ferias: no deployments en medio de una feria.
