from flask import Flask, send_from_directory, request, jsonify
import ssl
import os
import ipaddress
import requests
import json
import sqlite3
import bcrypt
import mercadopago
import jwt
import datetime
import secrets
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

app = Flask(__name__, static_folder='.')

# JWT Secret Key
JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'tu_clave_secreta_muy_segura_aqui')

@app.after_request
def add_security_headers(response):
    response.headers['Content-Security-Policy'] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://accounts.google.com https://apis.google.com https://www.gstatic.com https://sdk.mercadopago.com blob: data:; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://accounts.google.com https://www.gstatic.com; "
        "font-src 'self' https://fonts.gstatic.com; "
        "img-src 'self' data: https:; "
        "connect-src 'self' https://accounts.google.com https://www.googleapis.com https://api.mercadopago.com; "
        "frame-src https://accounts.google.com https://www.mercadopago.com.ar;"
    )
    response.headers['Cross-Origin-Opener-Policy'] = 'unsafe-none'
    return response

# Database setup
def init_db():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  name TEXT NOT NULL,
                  email TEXT UNIQUE NOT NULL,
                  password_hash TEXT NOT NULL,
                  reset_token TEXT,
                  reset_token_expiry DATETIME)''')
    conn.commit()
    conn.close()

# Initialize database on startup
init_db()

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/<path:filename>')
def serve_file(filename):
    return send_from_directory('.', filename)

@app.route('/success.html')
def success_page():
    return send_from_directory('.', 'success.html')

@app.route('/api/auth/google', methods=['POST'])
def google_auth():
    data = request.get_json()
    if not data or 'credential' not in data:
        return jsonify({'success': False, 'message': 'Token no proporcionado'}), 400

    try:
        # Verificar el token de Google
        from google.auth import jwt
        from google.auth.transport import requests as google_requests

        # Decodificar el JWT sin verificar (para desarrollo; en producción, verifica con Google)
        decoded = jwt.decode(data['credential'], options={"verify_signature": False})

        # En producción, deberías verificar el token con Google
        # Aquí simulamos validación básica
        if decoded.get('iss') == 'https://accounts.google.com' and decoded.get('aud') == GOOGLE_CLIENT_ID:
            # Verificar que el email esté presente
            user_email = decoded.get('email')
            if not user_email:
                return jsonify({'success': False, 'message': 'Email no encontrado en el token'}), 400

            # Generar JWT token
            token_payload = {
                'user_id': decoded.get('sub', user_email),
                'email': user_email,
                'name': decoded.get('name'),
                'exp': datetime.datetime.utcnow() + datetime.timedelta(days=7)
            }
            token = jwt.encode(token_payload, JWT_SECRET_KEY, algorithm='HS256')

            return jsonify({
                'success': True,
                'message': 'Autenticación exitosa',
                'token': token,
                'user': {
                    'name': decoded.get('name'),
                    'email': user_email,
                    'picture': decoded.get('picture')
                }
            })
        else:
            return jsonify({'success': False, 'message': 'Token inválido'}), 400
    except Exception as e:
        print(f"Error en autenticación Google: {str(e)}")
        return jsonify({'success': False, 'message': 'Error en autenticación'}), 500

@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')

    if not name or not email or not password:
        return jsonify({'success': False, 'message': 'Todos los campos son requeridos'}), 400

    if len(password) < 6:
        return jsonify({'success': False, 'message': 'La contraseña debe tener al menos 6 caracteres'}), 400

    # Hash the password
    password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

    try:
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        c.execute('INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)',
                  (name, email, password_hash.decode('utf-8')))
        conn.commit()
        conn.close()

        # Generar JWT token
        token_payload = {
            'user_id': email,
            'email': email,
            'name': name,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(days=7)
        }
        token = jwt.encode(token_payload, JWT_SECRET_KEY, algorithm='HS256')

        return jsonify({'success': True, 'message': 'Usuario registrado exitosamente', 'token': token})
    except sqlite3.IntegrityError:
        return jsonify({'success': False, 'message': 'El email ya está registrado'}), 400
    except Exception as e:
        return jsonify({'success': False, 'message': 'Error interno del servidor'}), 500

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({'success': False, 'message': 'Email y contraseña son requeridos'}), 400

    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('SELECT id, name, password_hash FROM users WHERE email = ?', (email,))
    user = c.fetchone()
    conn.close()

    if user and bcrypt.checkpw(password.encode('utf-8'), user[2].encode('utf-8')):
        # Generar JWT token
        token_payload = {
            'user_id': user[0],
            'email': email,
            'name': user[1],
            'exp': datetime.datetime.utcnow() + datetime.timedelta(days=7)
        }
        token = jwt.encode(token_payload, JWT_SECRET_KEY, algorithm='HS256')

        return jsonify({'success': True, 'message': 'Inicio de sesión exitoso', 'token': token, 'user': {'id': user[0], 'name': user[1], 'email': email}})
    else:
        return jsonify({'success': False, 'message': 'Credenciales inválidas'}), 401

# Middleware para verificar JWT
def verify_token():
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return None

    token = auth_header.split(' ')[1]
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

# Configuración de Mercado Pago
MERCADO_PAGO_ACCESS_TOKEN = os.environ.get('MERCADO_PAGO_ACCESS_TOKEN', 'APP_USR-3539367639762246-102102-0f43deb9e987a46b1829d95cbbe0ced3-301099354')
sdk = mercadopago.SDK(MERCADO_PAGO_ACCESS_TOKEN)

# Configuración de Google OAuth
GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID', '834692381201-sa5mpbj4mjrucgkslgf0oacdn40p6794.apps.googleusercontent.com')
GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET', '****VaJN')

# Configuración de email para recuperación de contraseña
SMTP_SERVER = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
SMTP_PORT = int(os.environ.get('SMTP_PORT', 587))
SMTP_USERNAME = os.environ.get('SMTP_USERNAME', 'tu-email@gmail.com')
SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD', 'tu-contraseña-app')
FROM_EMAIL = os.environ.get('FROM_EMAIL', 'tu-email@gmail.com')

@app.route('/api/create_preference', methods=['POST'])
def create_preference():
    """Crear preferencia de pago para Mercado Pago"""
    # Verificar autenticación
    user = verify_token()
    if not user:
        return jsonify({'success': False, 'message': 'Autenticación requerida'}), 401

    data = request.get_json()
    beat_name = data.get('beat_name')
    beat_price = data.get('beat_price', 0)

    if not beat_name or beat_price <= 0:
        return jsonify({'success': False, 'message': 'Datos de beat inválidos'}), 400

    # Obtener URL base para callbacks
    base_url = request.host_url.rstrip('/')

    # Crear preferencia de pago
    preference_data = {
        "items": [
            {
                "title": f"Beat: {beat_name}",
                "quantity": 1,
                "unit_price": float(beat_price.replace('$', '').replace(',', ''))
            }
        ],
        "back_urls": {
            "success": f"{base_url}/success.html",
            "failure": f"{base_url}/checkout.html",
            "pending": f"{base_url}/checkout.html"
        },
        "auto_return": "approved",
        "external_reference": f"{user['user_id']}_{beat_name}"
    }

    try:
        preference_response = sdk.preference().create(preference_data)
        preference = preference_response["response"]

        return jsonify({
            'success': True,
            'preference_id': preference['id'],
            'init_point': preference['init_point']
        })
    except Exception as e:
        print(f"Error creando preferencia: {str(e)}")
        return jsonify({'success': False, 'message': 'Error creando preferencia de pago'}), 500

@app.route('/api/payment_notification', methods=['POST'])
def payment_notification():
    """Webhook para notificaciones de Mercado Pago"""
    data = request.get_json()

    # Verificar que la solicitud provenga de Mercado Pago (básica)
    # En producción, implementar verificación de firma HMAC
    if not data:
        return jsonify({'status': 'error', 'message': 'No data received'}), 400

    if data.get('type') == 'payment':
        payment_id = data.get('data', {}).get('id')

        if payment_id:
            try:
                # Obtener detalles del pago desde Mercado Pago
                payment_info = sdk.payment().get(payment_id)
                payment_data = payment_info['response']

                # Verificar estado del pago
                status = payment_data.get('status')
                external_reference = payment_data.get('external_reference')

                print(f"Notificación de pago recibida: ID {payment_id}, Estado: {status}, Referencia: {external_reference}")

                # Aquí puedes actualizar tu base de datos según el estado del pago
                # Por ejemplo, marcar como pagado, enviar email de confirmación, etc.

                if status == 'approved':
                    print(f"Pago aprobado para: {external_reference}")
                    # Actualizar base de datos: marcar como vendido, enviar beat por email, etc.
                elif status == 'rejected':
                    print(f"Pago rechazado para: {external_reference}")
                elif status == 'pending':
                    print(f"Pago pendiente para: {external_reference}")

            except Exception as e:
                print(f"Error procesando notificación de pago: {str(e)}")
                return jsonify({'status': 'error', 'message': 'Error processing payment'}), 500

    return jsonify({'status': 'ok'}), 200

def send_reset_email(email, reset_token):
    """Enviar email con clave temporal para recuperación de contraseña"""
    try:
        msg = MIMEMultipart()
        msg['From'] = FROM_EMAIL
        msg['To'] = email
        msg['Subject'] = 'Recuperación de Contraseña - Majestic Beats'

        body = f"""
        Hola,

        Has solicitado recuperar tu contraseña en Majestic Beats.

        Tu clave temporal es: {reset_token}

        Esta clave es válida por 1 hora. Por favor, ingrésala en la página de restablecimiento de contraseña junto con tu nueva contraseña.

        Si no solicitaste este cambio, ignora este mensaje.

        Saludos,
        El equipo de Majestic Beats
        """

        msg.attach(MIMEText(body, 'plain'))

        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        text = msg.as_string()
        server.sendmail(FROM_EMAIL, email, text)
        server.quit()

        return True
    except Exception as e:
        print(f"Error enviando email: {str(e)}")
        return False

@app.route('/api/forgot_password', methods=['POST'])
def forgot_password():
    """Solicitar recuperación de contraseña"""
    data = request.get_json()
    email = data.get('email')

    if not email:
        return jsonify({'success': False, 'message': 'Email es requerido'}), 400

    # Verificar si el usuario existe
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('SELECT id FROM users WHERE email = ?', (email,))
    user = c.fetchone()

    if not user:
        # No revelar si el email existe o no por seguridad
        return jsonify({'success': True, 'message': 'Si el email existe, recibirás instrucciones para recuperar tu contraseña'}), 200

    # Generar clave temporal única de 9 caracteres
    reset_token = secrets.token_urlsafe(6)[:9]  # Genera al menos 9 caracteres seguros

    # Establecer expiración en 1 hora
    expiry = datetime.datetime.utcnow() + datetime.timedelta(hours=1)

    # Guardar token en la base de datos
    c.execute('UPDATE users SET reset_token = ?, reset_token_expiry = ? WHERE email = ?',
              (reset_token, expiry, email))
    conn.commit()
    conn.close()

    # Enviar email
    if send_reset_email(email, reset_token):
        return jsonify({'success': True, 'message': 'Si el email existe, recibirás instrucciones para recuperar tu contraseña'}), 200
    else:
        return jsonify({'success': False, 'message': 'Error enviando email. Inténtalo de nuevo más tarde'}), 500

@app.route('/api/reset_password', methods=['POST'])
def reset_password():
    """Restablecer contraseña usando clave temporal"""
    data = request.get_json()
    temp_password = data.get('temp_password')
    new_password = data.get('new_password')

    if not temp_password or not new_password:
        return jsonify({'success': False, 'message': 'Clave temporal y nueva contraseña son requeridas'}), 400

    if len(new_password) < 6:
        return jsonify({'success': False, 'message': 'La contraseña debe tener al menos 6 caracteres'}), 400

    # Verificar token
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('SELECT id FROM users WHERE reset_token = ? AND reset_token_expiry > ?',
              (temp_password, datetime.datetime.utcnow()))
    user = c.fetchone()

    if not user:
        conn.close()
        return jsonify({'success': False, 'message': 'Clave temporal inválida o expirada'}), 400

    # Hash de la nueva contraseña
    password_hash = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())

    # Actualizar contraseña y limpiar token
    c.execute('UPDATE users SET password_hash = ?, reset_token = NULL, reset_token_expiry = NULL WHERE reset_token = ?',
              (password_hash.decode('utf-8'), temp_password))
    conn.commit()
    conn.close()

    return jsonify({'success': True, 'message': 'Contraseña restablecida exitosamente'}), 200

@app.route('/api/download/<transaction_id>')
def download_beat(transaction_id):
    """Descargar beat después de pago exitoso"""
    # Verificar autenticación
    user = verify_token()
    if not user:
        return jsonify({'error': 'Autenticación requerida'}), 401

    # En producción, verificaría que la transacción existe y es válida
    # Por ahora, simulamos descarga basada en el transaction_id

    # Mapear nombres de beats a archivos reales
    beat_mapping = {
        'Beat Verano Reggaeton': 'BEATS/BEAT VERANO REGGEATON.mp3',
        'Beat 2025 Verano Trap': 'BEATS/BEAT 2025 VERANO TRAP HOUSE.mp3',
        'Beat Rellax Reggaeton': 'BEATS/BEAT RELLAX REGGEATON.mp3',
        'Beat Hip Hop Piano Gigant': 'BEATS/BEAT HIP HOP PIANO GIGANT.mp3',
        'Beat Sin Frontera': 'BEATS/BEAT SIN FRONTERA.mp3',
        'Beat Trap Navideño Chilling': 'BEATS/BEAT TRAP NAVIDEÑO CHILLING.mp3'
    }

    # Obtener beat desde parámetros de URL
    beat_name = request.args.get('beat', 'Beat Verano Reggaeton')
    beat_file = beat_mapping.get(beat_name, 'BEATS/BEAT VERANO REGGEATON.mp3')

    if os.path.exists(beat_file):
        return send_from_directory('.', beat_file, as_attachment=True, download_name=f"{beat_name}.mp3")
    else:
        return jsonify({'error': 'Beat no encontrado'}), 404

if __name__ == '__main__':
    # Para desarrollo local con HTTPS y certificados de confianza
    import os
    import subprocess

    # Obtener puerto desde variable de entorno (para despliegue en la nube)
    port = int(os.environ.get('PORT', 5000))

    # Configurar URLs para Google OAuth
    if port == 5000:
        oauth_url = "https://localhost:5000"
    else:
        # Para despliegue en la nube, la URL se debe configurar manualmente
        oauth_url = os.environ.get('OAUTH_URL', 'https://web-production-f58b3.up.railway.app')

    print(f"🌐 URL para Google OAuth: {oauth_url}")
    print("📝 Agrega esta URL a los orígenes autorizados en Google Cloud Console")

    # Para desarrollo local (puerto 5000), usar HTTPS con mkcert
    if port == 5000:
        # Instalar mkcert si no está disponible
        try:
            subprocess.run(['mkcert', '--version'], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("Instalando mkcert...")
            # Descargar mkcert
            import urllib.request
            import zipfile
            import platform

            system = platform.system().lower()
            if system == 'windows':
                url = 'https://github.com/FiloSottile/mkcert/releases/latest/download/mkcert-v1.4.4-windows-amd64.exe'
                filename = 'mkcert.exe'
            elif system == 'linux':
                url = 'https://github.com/FiloSottile/mkcert/releases/latest/download/mkcert-v1.4.4-linux-amd64'
                filename = 'mkcert'
            elif system == 'darwin':
                url = 'https://github.com/FiloSottile/mkcert/releases/latest/download/mkcert-v1.4.4-darwin-amd64'
                filename = 'mkcert'
            else:
                print("Sistema operativo no soportado para instalación automática de mkcert")
                exit(1)

            try:
                urllib.request.urlretrieve(url, filename)
                os.chmod(filename, 0o755)
                print("mkcert instalado correctamente")
            except Exception as e:
                print(f"Error instalando mkcert: {e}")
                print("Continuando sin mkcert...")

        # Instalar CA de mkcert
        try:
            subprocess.run(['./mkcert', '-install'], check=True, capture_output=True)
            print("CA de mkcert instalado correctamente")
        except subprocess.CalledProcessError:
            print("Error instalando CA de mkcert - puedes ignorar si ya está instalado")

        # Generar certificados para localhost
        cert_file = 'localhost.pem'
        key_file = 'localhost-key.pem'

        if not os.path.exists(cert_file) or not os.path.exists(key_file):
            try:
                subprocess.run(['./mkcert', '-cert-file', cert_file, '-key-file', key_file, 'localhost', '127.0.0.1'], check=True, capture_output=True)
                print("Certificados SSL generados correctamente")
            except subprocess.CalledProcessError:
                print("Error generando certificados SSL - usando certificados existentes si están disponibles")

        # Ejecutar servidor HTTPS
        if os.path.exists(cert_file) and os.path.exists(key_file):
            context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            context.load_cert_chain(cert_file, key_file)

            print("🚀 Servidor HTTPS ejecutándose en https://localhost:5000")
            print("⚠️  IMPORTANTE: Si ves advertencias de certificado, acepta el certificado de mkcert")
            print("🔐 Google OAuth funcionará correctamente con HTTPS")
            print("🌐 Para Google OAuth, asegúrate de agregar https://localhost:5000 a los orígenes autorizados en Google Cloud Console")
            app.run(host='localhost', port=port, ssl_context=context, debug=True)
        else:
            print("❌ No se pudieron generar los certificados. Ejecutando en HTTP...")
            print("⚠️  Google OAuth NO funcionará en HTTP - necesitas HTTPS")
            print("💡 Ejecuta: mkcert -install && mkcert -cert-file localhost.pem -key-file localhost-key.pem localhost 127.0.0.1")
            app.run(host='localhost', port=port, debug=True)
    else:
        # Para despliegue en la nube (puerto dinámico), usar HTTP (la nube maneja HTTPS)
        print(f"🚀 Servidor ejecutándose en puerto {port} (modo nube)")
        print("🌐 Para Google OAuth, asegúrate de agregar la URL de tu aplicación en la nube a los orígenes autorizados en Google Cloud Console")
        app.run(host='0.0.0.0', port=port, debug=False)
