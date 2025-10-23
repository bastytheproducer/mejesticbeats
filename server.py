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
    response.headers['Cross-Origin-Opener-Policy'] = 'same-origin'
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
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

    # Crear tabla de beats con stock
    c.execute('''CREATE TABLE IF NOT EXISTS beats
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  name TEXT UNIQUE NOT NULL,
                  price TEXT NOT NULL,
                  genre TEXT NOT NULL,
                  file_path TEXT NOT NULL,
                  image_path TEXT NOT NULL,
                  stock INTEGER DEFAULT 1,
                  sold BOOLEAN DEFAULT 0,
                  sold_date DATETIME,
                  buyer_email TEXT)''')

    # Insertar beats iniciales si no existen
    beats_data = [
        ('Beat Verano Reggaeton', '$20.000 CLP', 'Reggaeton', 'BEATS/BEAT VERANO REGGEATON.mp3', 'Caratulas de lo beats/beat verano reggeaton.png'),
        ('Beat 2025 Verano Trap', '$25.000 CLP', 'Trap', 'BEATS/BEAT 2025 VERANO TRAP HOUSE.mp3', 'Caratulas de lo beats/Beat 2025 verano trap.png'),
        ('Beat Rellax Reggaeton', '$22.000 CLP', 'Reggaeton Relax', 'BEATS/BEAT RELLAX REGGEATON.mp3', 'Caratulas de lo beats/beat rellax reggeaton.png'),
        ('Beat Hip Hop Piano Gigant', '$28.000 CLP', 'Hip Hop', 'BEATS/BEAT HIP HOP PIANO GIGANT.mp3', 'Caratulas de lo beats/beat hip hop piano gigant.jpg'),
        ('Beat Sin Frontera', '$30.000 CLP', 'Instrumental', 'BEATS/BEAT SIN FRONTERA.mp3', 'Caratulas de lo beats/beat sin frontera.png'),
        ('Beat Trap Navideño Chilling', '$26.000 CLP', 'Trap Navideño', 'BEATS/BEAT TRAP NAVIDEÑO CHILLING.mp3', 'Caratulas de lo beats/beat trap navideño chilling.png')
    ]

    for beat in beats_data:
        c.execute('INSERT OR IGNORE INTO beats (name, price, genre, file_path, image_path) VALUES (?, ?, ?, ?, ?)', beat)

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
    c.execute('SELECT id, name, password_hash, reset_token FROM users WHERE email = ?', (email,))
    user = c.fetchone()
    conn.close()

    if user:
        # Verificar si es una clave temporal
        if user[3] and user[3] == password:
            # Es una clave temporal, redirigir a cambio de contraseña
            token_payload = {
                'user_id': user[0],
                'email': email,
                'name': user[1],
                'temp_password': True,
                'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1)
            }
            token = jwt.encode(token_payload, JWT_SECRET_KEY, algorithm='HS256')
            return jsonify({
                'success': True,
                'message': 'Clave temporal detectada. Redirigiendo a cambio de contraseña.',
                'token': token,
                'redirect_to': 'change_password.html'
            }), 200
        elif bcrypt.checkpw(password.encode('utf-8'), user[2].encode('utf-8')):
            # Contraseña normal correcta
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

# Configuración de Mercado Pago (Chile)
MERCADO_PAGO_ACCESS_TOKEN = os.environ.get('MERCADO_PAGO_ACCESS_TOKEN', 'TU_ACCESS_TOKEN_DE_MERCADO_PAGO_CHILE_AQUI')
sdk = mercadopago.SDK(MERCADO_PAGO_ACCESS_TOKEN)

# Configuración de Transbank (placeholders)
TRANSBANK_API_KEY = os.environ.get('TRANSBANK_API_KEY', 'TU_API_KEY_DE_TRANSBANK_AQUI')
TRANSBANK_COMMERCE_CODE = os.environ.get('TRANSBANK_COMMERCE_CODE', 'TU_CODIGO_DE_COMERCIO_AQUI')
TRANSBANK_ENVIRONMENT = os.environ.get('TRANSBANK_ENVIRONMENT', 'TEST')  # 'TEST' o 'LIVE'

# Configuración de Google OAuth
GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID', '834692381201-sa5mpbj4mjrucgkslgf0oacdn40p6794.apps.googleusercontent.com')
GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET', '****VaJN')

# Configuración de email para recuperación de contraseña
SMTP_SERVER = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
SMTP_PORT = int(os.environ.get('SMTP_PORT', 587))
SMTP_USERNAME = os.environ.get('SMTP_USERNAME', 'tu-email@gmail.com')
SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD', 'tu-contraseña-app')
FROM_EMAIL = os.environ.get('FROM_EMAIL', 'tu-email@gmail.com')

# Modo desarrollo para emails
DEV_MODE = os.environ.get('DEV_MODE', 'true').lower() == 'true'

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
        "external_reference": f"{user['user_id']}_{beat_name}",
        "marketplace_fee": 0  # Sin comisión de marketplace
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
    if DEV_MODE:
        print(f"DEV MODE: Reset token for {email}: {reset_token}")
        print("DEV MODE: Email sending bypassed. Use this token to reset password.")
        return True

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

        print(f"Email sent successfully to {email}")
        return True
    except Exception as e:
        print(f"Error enviando email: {str(e)}")
        return False

@app.route('/api/forgot_password', methods=['POST', 'OPTIONS'])
def forgot_password():
    """Solicitar recuperación de contraseña"""
    if request.method == 'OPTIONS':
        return jsonify({'success': True}), 200

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
        message = 'Si el email existe, recibirás instrucciones para recuperar tu contraseña'
        if DEV_MODE:
            message += ' (En modo desarrollo, revisa la consola del servidor para el token)'
        return jsonify({'success': True, 'message': message}), 200

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
        message = 'Si el email existe, recibirás instrucciones para recuperar tu contraseña'
        if DEV_MODE:
            message += ' (En modo desarrollo, revisa la consola del servidor para el token)'
        return jsonify({'success': True, 'message': message}), 200
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

@app.route('/api/change_password', methods=['POST'])
def change_password():
    """Cambiar contraseña para usuarios con clave temporal"""
    # Verificar autenticación
    user = verify_token()
    if not user:
        return jsonify({'success': False, 'message': 'Autenticación requerida'}), 401

    # Verificar que sea un usuario con clave temporal
    if not user.get('temp_password'):
        return jsonify({'success': False, 'message': 'Esta función es solo para usuarios con clave temporal'}), 403

    data = request.get_json()
    new_password = data.get('new_password')

    if not new_password:
        return jsonify({'success': False, 'message': 'Nueva contraseña requerida'}), 400

    if len(new_password) < 6:
        return jsonify({'success': False, 'message': 'La contraseña debe tener al menos 6 caracteres'}), 400

    # Hash de la nueva contraseña
    password_hash = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())

    # Actualizar contraseña y limpiar token temporal
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('UPDATE users SET password_hash = ?, reset_token = NULL, reset_token_expiry = NULL WHERE id = ?',
              (password_hash.decode('utf-8'), user['user_id']))
    conn.commit()
    conn.close()

    return jsonify({'success': True, 'message': 'Contraseña cambiada exitosamente'}), 200

@app.route('/api/create_transbank_transaction', methods=['POST'])
def create_transbank_transaction():
    """Crear transacción de Transbank (placeholders)"""
    # Verificar autenticación
    user = verify_token()
    if not user:
        return jsonify({'success': False, 'message': 'Autenticación requerida'}), 401

    data = request.get_json()
    beat_name = data.get('beat_name')
    beat_price = data.get('beat_price', 0)

    if not beat_name or beat_price <= 0:
        return jsonify({'success': False, 'message': 'Datos de beat inválidos'}), 400

    # Placeholder para integración con Transbank
    # En producción, aquí iría la lógica para crear la transacción con la API de Transbank
    # Usando TRANSBANK_API_KEY, TRANSBANK_COMMERCE_CODE, etc.

    # Simular respuesta exitosa con placeholders
    return jsonify({
        'success': True,
        'redirect_url': 'https://webpay3g.transbank.cl/webpayserver/initTransaction',  # Placeholder
        'token': 'PLACEHOLDER_TOKEN_TRANSBANK'  # Placeholder
    })

@app.route('/api/beats')
def get_beats():
    """Obtener lista de beats disponibles (no vendidos)"""
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('SELECT name, price, genre, image_path FROM beats WHERE sold = 0 ORDER BY id')
    beats = c.fetchall()
    conn.close()

    beats_list = []
    for beat in beats:
        beats_list.append({
            'name': beat[0],
            'price': beat[1],
            'genre': beat[2],
            'image': beat[3]
        })

    return jsonify({'beats': beats_list})

@app.route('/api/check_stock/<beat_name>')
def check_stock(beat_name):
    """Verificar si un beat está disponible"""
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('SELECT stock, sold FROM beats WHERE name = ?', (beat_name,))
    beat = c.fetchone()
    conn.close()

    if beat:
        available = beat[0] > 0 and not beat[1]
        return jsonify({'available': available, 'stock': beat[0], 'sold': beat[1]})
    else:
        return jsonify({'available': False, 'stock': 0, 'sold': False}), 404

@app.route('/api/mark_sold/<beat_name>', methods=['POST'])
def mark_beat_sold(beat_name):
    """Marcar un beat como vendido"""
    # Verificar autenticación
    user = verify_token()
    if not user:
        return jsonify({'success': False, 'message': 'Autenticación requerida'}), 401

    data = request.get_json()
    buyer_email = data.get('buyer_email', user.get('email'))

    conn = sqlite3.connect('users.db')
    c = conn.cursor()

    # Verificar que el beat existe y no está vendido
    c.execute('SELECT id, stock FROM beats WHERE name = ? AND sold = 0', (beat_name,))
    beat = c.fetchone()

    if not beat:
        conn.close()
        return jsonify({'success': False, 'message': 'Beat no disponible'}), 404

    # Marcar como vendido
    c.execute('''UPDATE beats SET sold = 1, sold_date = ?, buyer_email = ?, stock = 0
                 WHERE name = ?''',
              (datetime.datetime.utcnow(), buyer_email, beat_name))

    conn.commit()
    conn.close()

    return jsonify({'success': True, 'message': 'Beat marcado como vendido'})

@app.route('/api/download/<transaction_id>')
def download_beat(transaction_id):
    """Descargar beat después de pago exitoso"""
    # Verificar autenticación
    user = verify_token()
    if not user:
        return jsonify({'error': 'Autenticación requerida'}), 401

    beat_name = request.args.get('beat')

    if not beat_name:
        return jsonify({'error': 'Nombre del beat requerido'}), 400

    # Verificar que el usuario compró este beat
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('SELECT file_path FROM beats WHERE name = ? AND buyer_email = ? AND sold = 1',
              (beat_name, user['email']))
    beat = c.fetchone()
    conn.close()

    if not beat:
        return jsonify({'error': 'Beat no encontrado o no autorizado'}), 404

    beat_file = beat[0]

    if os.path.exists(beat_file):
        return send_from_directory('.', beat_file, as_attachment=True, download_name=f"{beat_name}.mp3")
    else:
        return jsonify({'error': 'Archivo no encontrado'}), 404

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
            print("mkcert no está instalado. Para desarrollo local con HTTPS, instala mkcert manualmente.")
            print("Instrucciones: https://github.com/FiloSottile/mkcert")

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
