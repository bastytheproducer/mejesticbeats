from flask import Flask, send_from_directory, request, jsonify, abort
from werkzeug.middleware.proxy_fix import ProxyFix
import os
import re
import urllib.parse
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
from google.oauth2 import id_token as google_id_token
from google.auth.transport import requests as google_requests

# static_folder=None: sin esto Flask publica toda la carpeta del proyecto
# por una ruta estática propia, saltándose la lista de permitidos.
app = Flask(__name__, static_folder=None)
# Detrás del proxy del hosting (Railway): respeta https y el dominio real.
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
app.config['MAX_CONTENT_LENGTH'] = 60 * 1024 * 1024  # tope de subida: 60 MB

# Clave para firmar las sesiones (JWT). Debe venir de la variable de entorno
# JWT_SECRET_KEY; nunca se deja una clave fija en el código, porque cualquiera
# que lea el repositorio podría fabricar sesiones válidas.
JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY')
if not JWT_SECRET_KEY:
    JWT_SECRET_KEY = secrets.token_urlsafe(48)
    print("AVISO: falta JWT_SECRET_KEY. Se generó una clave temporal: "
          "las sesiones se cerrarán cada vez que el servidor se reinicie.")

# Carpeta con los MP3 completos. No es pública ni va al repositorio:
# solo se entrega un archivo después de verificar el pago.
# DATA_DIR es la carpeta persistente del hosting (en Railway, un volumen
# montado por ejemplo en /data). Ahí viven la base de datos y los MP3 completos.
DATA_DIR = os.environ.get('DATA_DIR', '.')
os.makedirs(DATA_DIR, exist_ok=True)
DB_PATH = os.path.join(DATA_DIR, 'users.db')
PRIVATE_BEATS_DIR = os.environ.get('PRIVATE_BEATS_DIR', os.path.join(DATA_DIR, 'beats_privados'))
os.makedirs(PRIVATE_BEATS_DIR, exist_ok=True)

# Clave para subir los MP3 completos desde admin.html. Sin ella, la subida queda desactivada.
ADMIN_TOKEN = os.environ.get('ADMIN_TOKEN', '')

# Lo único que el servidor entrega como archivo estático.
PUBLIC_EXTENSIONS = {'.html', '.css', '.js', '.png', '.jpg', '.jpeg', '.webp', '.svg', '.ico'}
PUBLIC_AUDIO_DIR = 'previews'  # adelantos de 45 segundos

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
    conn = sqlite3.connect(DB_PATH)
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
    # Lista de permitidos: sin esto se podían descargar users.db, server.py,
    # las llaves .pem y los MP3 completos con solo escribir su nombre.
    normalized = os.path.normpath(filename).replace('\\', '/')
    parts = normalized.split('/')
    if normalized.startswith('/') or any(p in ('', '..') or p.startswith('.') for p in parts):
        abort(404)
    ext = os.path.splitext(normalized)[1].lower()
    is_public = ext in PUBLIC_EXTENSIONS or (ext == '.mp3' and parts[0] == PUBLIC_AUDIO_DIR)
    if not is_public or parts[0] in ('beats_privados', 'BEATS'):
        abort(404)
    return send_from_directory('.', normalized)

@app.route('/success.html')
def success_page():
    return send_from_directory('.', 'success.html')

@app.route('/api/auth/google', methods=['POST'])
def google_auth():
    data = request.get_json()
    if not data or 'credential' not in data:
        return jsonify({'success': False, 'message': 'Token no proporcionado'}), 400

    try:
        # Verificar firma, emisor, audiencia y vencimiento del token con Google
        decoded = google_id_token.verify_oauth2_token(
            data['credential'], google_requests.Request(), GOOGLE_CLIENT_ID)
    except ValueError:
        return jsonify({'success': False, 'message': 'Token inválido'}), 400

    try:
        user_email = decoded.get('email')
        if not user_email or not decoded.get('email_verified'):
            return jsonify({'success': False, 'message': 'Email no verificado en el token'}), 400

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
        conn = sqlite3.connect(DB_PATH)
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

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT id, name, password_hash, reset_token, reset_token_expiry FROM users WHERE email = ?', (email,))
    user = c.fetchone()
    conn.close()

    if user:
        # Verificar si es una clave temporal (solo mientras no haya vencido)
        temp_valid = bool(user[3]) and bool(user[4]) and str(user[4]) > str(datetime.datetime.utcnow())
        if temp_valid and secrets.compare_digest(str(user[3]), password):
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
GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET', '')

# Configuración de email para recuperación de contraseña
SMTP_SERVER = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
SMTP_PORT = int(os.environ.get('SMTP_PORT', 587))
SMTP_USERNAME = os.environ.get('SMTP_USERNAME', 'tu-email@gmail.com')
SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD', 'tu-contraseña-app')
FROM_EMAIL = os.environ.get('FROM_EMAIL', 'tu-email@gmail.com')

# Modo desarrollo para emails
DEV_MODE = os.environ.get('DEV_MODE', 'true').lower() == 'true'

def parse_price_clp(text):
    """'$30.000 CLP' -> 30000"""
    digits = re.sub(r'\D', '', text or '')
    return int(digits) if digits else 0

def make_reference(email, beat_name):
    return f"{email}|{beat_name}"

def confirm_payment(payment_id, expected_email=None, expected_beat=None):
    """Consulta el pago directamente en Mercado Pago y, si está aprobado y
    corresponde, marca el beat como vendido a ese comprador.
    Devuelve (True, nombre_del_beat) o (False, motivo)."""
    if not payment_id or not str(payment_id).isdigit():
        return False, 'Identificador de pago inválido'
    try:
        info = sdk.payment().get(payment_id)
    except Exception as e:
        print(f"Error consultando pago {payment_id}: {e}")
        return False, 'No se pudo verificar el pago'

    payment = info.get('response') or {}
    if info.get('status') != 200 or payment.get('status') != 'approved':
        return False, 'El pago no está aprobado'

    reference = payment.get('external_reference') or ''
    if '|' not in reference:
        return False, 'Pago sin referencia válida'
    email, beat_name = reference.split('|', 1)
    if expected_email and email != expected_email:
        return False, 'El pago pertenece a otra cuenta'
    if expected_beat and beat_name != expected_beat:
        return False, 'El pago corresponde a otro beat'

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT price, sold, buyer_email FROM beats WHERE name = ?', (beat_name,))
    beat = c.fetchone()
    if not beat:
        conn.close()
        return False, 'Beat no encontrado'
    if float(payment.get('transaction_amount') or 0) < parse_price_clp(beat[0]):
        conn.close()
        return False, 'El monto pagado no coincide con el precio'
    if beat[1] and beat[2] != email:
        conn.close()
        print(f"ATENCIÓN: pago {payment_id} aprobado para '{beat_name}', que ya estaba vendido. Requiere reembolso manual a {email}.")
        return False, 'Este beat ya fue vendido a otra persona'
    if not beat[1]:
        c.execute('UPDATE beats SET sold = 1, sold_date = ?, buyer_email = ?, stock = 0 WHERE name = ? AND sold = 0',
                  (datetime.datetime.utcnow(), email, beat_name))
        conn.commit()
    conn.close()
    return True, beat_name

@app.route('/api/create_preference', methods=['POST'])
def create_preference():
    """Crear preferencia de pago para Mercado Pago"""
    # Verificar autenticación
    user = verify_token()
    if not user:
        return jsonify({'success': False, 'message': 'Autenticación requerida'}), 401

    data = request.get_json(silent=True) or {}
    beat_name = data.get('beat_name')
    if not beat_name:
        return jsonify({'success': False, 'message': 'Datos de beat inválidos'}), 400

    # El precio se lee de la base de datos: lo que envíe el navegador no se usa,
    # así nadie puede pagar menos cambiando el monto.
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT price, stock, sold FROM beats WHERE name = ?', (beat_name,))
    beat = c.fetchone()
    conn.close()
    if not beat or beat[2] or beat[1] <= 0:
        return jsonify({'success': False, 'message': 'Este beat ya no está disponible'}), 404

    unit_price = parse_price_clp(beat[0])
    if unit_price <= 0:
        return jsonify({'success': False, 'message': 'Precio no configurado'}), 500

    # Obtener URL base para callbacks
    base_url = request.host_url.rstrip('/')
    beat_query = urllib.parse.quote(beat_name)

    # Crear preferencia de pago
    preference_data = {
        "items": [
            {
                "title": f"Beat: {beat_name}",
                "quantity": 1,
                "currency_id": "CLP",
                "unit_price": unit_price
            }
        ],
        "back_urls": {
            "success": f"{base_url}/success.html?beat={beat_query}",
            "failure": f"{base_url}/checkout.html?beat={beat_query}",
            "pending": f"{base_url}/success.html?beat={beat_query}"
        },
        "auto_return": "approved",
        "notification_url": f"{base_url}/api/payment_notification",
        "external_reference": make_reference(user['email'], beat_name)
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
    data = request.get_json(silent=True) or {}

    # El contenido del aviso no se da por cierto: solo se toma el id del pago
    # y su estado real se consulta directamente en Mercado Pago.
    if data.get('type') == 'payment':
        payment_id = (data.get('data') or {}).get('id')
        ok, detail = confirm_payment(payment_id)
        print(f"Notificación de pago {payment_id}: {'vendido ' + detail if ok else detail}")

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
    conn = sqlite3.connect(DB_PATH)
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
    conn = sqlite3.connect(DB_PATH)
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
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('UPDATE users SET password_hash = ?, reset_token = NULL, reset_token_expiry = NULL WHERE id = ?',
              (password_hash.decode('utf-8'), user['user_id']))
    conn.commit()
    conn.close()

    return jsonify({'success': True, 'message': 'Contraseña cambiada exitosamente'}), 200

@app.route('/api/create_transbank_transaction', methods=['POST'])
def create_transbank_transaction():
    """Crear transacción de Transbank (placeholders)"""
    # Transbank todavía no está integrado. Antes devolvía un éxito falso.
    return jsonify({'success': False, 'message': 'Transbank no está disponible por ahora. Usa Mercado Pago.'}), 501

def admin_authorized():
    sent = request.headers.get('X-Admin-Token', '')
    return bool(ADMIN_TOKEN) and secrets.compare_digest(sent, ADMIN_TOKEN)

@app.route('/api/admin/beats')
def admin_list_beats():
    """Estado de cada beat: si su MP3 completo está en el servidor y si se vendió."""
    if not admin_authorized():
        return jsonify({'error': 'No autorizado'}), 401
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT name, file_path, sold, buyer_email FROM beats ORDER BY id')
    rows = c.fetchall()
    conn.close()
    return jsonify({'beats': [{
        'name': r[0],
        'file': os.path.basename(r[1]),
        'uploaded': os.path.exists(os.path.join(PRIVATE_BEATS_DIR, os.path.basename(r[1]))),
        'sold': bool(r[2]),
        'buyer_email': r[3]
    } for r in rows]})

@app.route('/api/admin/upload_beat', methods=['POST'])
def admin_upload_beat():
    """Subir el MP3 completo de un beat a la carpeta privada."""
    if not admin_authorized():
        return jsonify({'error': 'No autorizado'}), 401

    beat_name = request.form.get('beat', '')
    upload = request.files.get('file')
    if not upload:
        return jsonify({'error': 'Falta el archivo'}), 400

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT file_path FROM beats WHERE name = ?', (beat_name,))
    beat = c.fetchone()
    conn.close()
    if not beat:
        return jsonify({'error': 'Beat no encontrado'}), 404

    # Solo MP3, y siempre con el nombre que el servidor espera para ese beat
    header = upload.stream.read(3)
    upload.stream.seek(0)
    looks_like_mp3 = header[:3] == b'ID3' or (len(header) >= 2 and header[0] == 0xFF and header[1] & 0xE0 == 0xE0)
    if not (upload.filename or '').lower().endswith('.mp3') or not looks_like_mp3:
        return jsonify({'error': 'El archivo debe ser un MP3'}), 400

    upload.save(os.path.join(PRIVATE_BEATS_DIR, os.path.basename(beat[0])))
    return jsonify({'success': True, 'message': f'MP3 de {beat_name} guardado'})

@app.route('/api/beats')
def get_beats():
    """Obtener lista de beats disponibles (no vendidos)"""
    import urllib.parse

    conn = sqlite3.connect(DB_PATH)
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
            'image': urllib.parse.quote(beat[3])
        })

    return jsonify({'beats': beats_list})

@app.route('/api/check_stock/<beat_name>')
def check_stock(beat_name):
    """Verificar si un beat está disponible"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT stock, sold FROM beats WHERE name = ?', (beat_name,))
    beat = c.fetchone()
    conn.close()

    if beat:
        available = beat[0] > 0 and not beat[1]
        return jsonify({'available': available, 'stock': beat[0], 'sold': beat[1]})
    else:
        return jsonify({'available': False, 'stock': 0, 'sold': False}), 404

# Nota: se eliminó /api/mark_sold. Permitía que cualquier usuario registrado
# marcara un beat como comprado sin pagar y luego lo descargara. Ahora un beat
# solo se marca como vendido en confirm_payment(), tras verificar el pago.

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

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT file_path, sold, buyer_email FROM beats WHERE name = ?', (beat_name,))
    beat = c.fetchone()
    conn.close()

    if not beat:
        return jsonify({'error': 'Beat no encontrado'}), 404

    # Solo descarga quien lo compró. Si aún no está registrado como vendido a
    # este usuario, se verifica el pago directamente en Mercado Pago.
    already_owner = bool(beat[1]) and beat[2] == user.get('email')
    if not already_owner:
        ok, detail = confirm_payment(transaction_id, user.get('email'), beat_name)
        if not ok:
            return jsonify({'error': detail}), 403

    # Los MP3 completos viven en la carpeta privada, fuera de lo público
    file_name = os.path.basename(beat[0])
    if os.path.exists(os.path.join(PRIVATE_BEATS_DIR, file_name)):
        return send_from_directory(os.path.abspath(PRIVATE_BEATS_DIR), file_name, as_attachment=True, download_name=f"{beat_name}.mp3")
    print(f"ATENCIÓN: falta el archivo '{file_name}' en {PRIVATE_BEATS_DIR}/")
    return jsonify({'error': 'Archivo no encontrado. Escríbenos y te lo enviamos.'}), 404

if __name__ == '__main__':
    # Para desarrollo local con HTTPS y certificados de confianza

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

    # Para desarrollo local (puerto 5000), usar HTTP
    if port == 5000:
        print("🚀 Servidor HTTP ejecutándose en http://localhost:5000")
        print("⚠️  Google OAuth NO funcionará en HTTP - necesitas HTTPS para producción")
        app.run(host='localhost', port=port, debug=True)
    else:
        # Para despliegue en la nube (puerto dinámico), usar HTTP (la nube maneja HTTPS)
        print(f"🚀 Servidor ejecutándose en puerto {port} (modo nube)")
        print("🌐 Para Google OAuth, asegúrate de agregar la URL de tu aplicación en la nube a los orígenes autorizados en Google Cloud Console")
        app.run(host='0.0.0.0', port=port, debug=False)
