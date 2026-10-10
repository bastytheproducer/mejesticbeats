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
