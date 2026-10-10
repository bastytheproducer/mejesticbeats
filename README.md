# Majestic Beats

Tienda de beats exclusivos: catálogo con reproductor, cuentas de usuario y pago con Mercado Pago.

## Cómo está armado

- **Sitio público** (`index.html`, `styles.css`, `script.js`, `covers/`, `previews/`): funciona solo, por ejemplo en GitHub Pages. Sin servidor, el botón *Comprar* ofrece reservar por correo.
- **Servidor** (`server.py`, Flask): cuentas, pago con Mercado Pago y descarga del MP3 completo.

## Seguridad de los beats

- En el sitio solo hay **adelantos de 45 segundos** (`previews/`).
- Los **MP3 completos no van en el repositorio**. Se guardan en la carpeta `beats_privados/` del servidor (ignorada por git), con el mismo nombre de archivo que figura en la base de datos, por ejemplo `BEAT SIN FRONTERA.mp3`.
- El servidor entrega un MP3 completo solo después de verificar en Mercado Pago que el pago está aprobado, es de esa cuenta, de ese beat y por el precio correcto.

Para agregar un beat: guarda el MP3 completo en `beats_privados/`, crea su adelanto y agrégalo a `script.js` y a la lista de `server.py`.

```bash
ffmpeg -i "beats_privados/MI BEAT.mp3" -t 45 -af "afade=t=out:st=41:d=4" -map_metadata -1 -b:a 128k previews/mi-beat.mp3
```

## Variables de entorno del servidor

| Variable | Para qué |
| --- | --- |
| `JWT_SECRET_KEY` | Clave larga y aleatoria que firma las sesiones. Obligatoria en producción. |
| `MERCADO_PAGO_ACCESS_TOKEN` | Credencial de producción de Mercado Pago. |
| `GOOGLE_CLIENT_ID` | Inicio de sesión con Google. |
| `SMTP_SERVER`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`, `FROM_EMAIL` | Correo de recuperación de contraseña. |
| `DEV_MODE` | `false` en producción para que los correos se envíen de verdad. |
| `PRIVATE_BEATS_DIR` | Carpeta de los MP3 completos (por defecto `beats_privados`). |

Nunca subas al repositorio `users.db`, archivos `.pem`, `.env` ni los MP3 completos: `.gitignore` ya los excluye.

## Ejecutar en tu computador

```bash
pip install -r requirements.txt
python server.py   # http://localhost:5000
```

## Publicar el servidor en PythonAnywhere (gratis)

1. En una consola Bash de PythonAnywhere:

   ```bash
   git clone https://github.com/bastytheproducer/mejesticbeats.git
   pip install --user -r mejesticbeats/requirements.txt
   ```
2. Pestaña **Web** → *Add a new web app* → *Manual configuration* (misma versión de Python que usa `pip`).
3. De vuelta en la consola: `python3 ~/mejesticbeats/deploy/pythonanywhere_setup.py`. Muestra la clave del panel de administración una sola vez.
4. Pega tu Access Token de Mercado Pago en `~/majestic_data/secrets.py` y pulsa **Reload** en la pestaña Web.
5. Sube los MP3 completos en `https://TU_USUARIO.pythonanywhere.com/admin.html`.
6. Pon esa dirección en `config.js` para que la página de GitHub Pages lleve a la tienda.

Para actualizar después: `cd ~/mejesticbeats && git pull` y **Reload**. En el plan gratuito hay que entrar una vez al mes a la pestaña Web y pulsar *Run until 1 month from today*.
