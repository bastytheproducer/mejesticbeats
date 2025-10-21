from flask import Flask, send_from_directory, request, jsonify
import ssl
import os
import ipaddress
import requests
import json
import sqlite3
import bcrypt

app = Flask(__name__, static_folder='.')

@app.after_request
def add_security_headers(response):
    response.headers['Content-Security-Policy'] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://accounts.google.com https://apis.google.com https://www.gstatic.com blob: data:; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com; "
        "img-src 'self' data: https:; "
        "connect-src 'self' https://accounts.google.com https://www.googleapis.com; "
        "frame-src https://accounts.google.com;"
    )
    response.headers['Cross-Origin-Opener-Policy'] = 'same-origin-allow-popups'
    return response

# Database setup
def init_db():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  name TEXT NOT NULL,
                  email TEXT UNIQUE NOT NULL,
                  password_hash TEXT NOT NULL)''')
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

            return jsonify({
                'success': True,
                'message': 'Autenticación exitosa',
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
        return jsonify({'success': True, 'message': 'Usuario registrado exitosamente'})
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
        return jsonify({'success': True, 'message': 'Inicio de sesión exitoso', 'user': {'id': user[0], 'name': user[1], 'email': email}})
    else:
        return jsonify({'success': False, 'message': 'Credenciales inválidas'}), 401

# Configuración de Google OAuth
GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID', '834692381201-sa5mpbj4mjrucgkslgf0oacdn40p6794.apps.googleusercontent.com')
GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET', '****VaJN')







@app.route('/api/download/<transaction_id>')
def download_beat(transaction_id):
    """Descargar beat después de pago exitoso"""
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
