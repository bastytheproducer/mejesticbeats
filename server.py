from flask import Flask, send_from_directory, request, jsonify
import ssl
import os
import ipaddress
import requests
import json
import sqlite3
import bcrypt

app = Flask(__name__, static_folder='.')

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
    # Simular validación de token de Google
    if data and 'credential' in data:
        return jsonify({'success': True, 'message': 'Autenticación exitosa'})
    return jsonify({'success': False, 'message': 'Token inválido'}), 400

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

# Configuración de PayPal (Sandbox)
PAYPAL_CLIENT_ID = 'AbJCNysCeJwZ2g-62JxkTlxIb3NwDEZJW7ZBctPmPRWtKa16bMOnzD_9Dn9eJ4PZ2cXUT8CS4D_nzLhB'  # Client ID real
PAYPAL_CLIENT_SECRET = 'EHF7H-BJeoZtAAQzFG2NqWlZVfEOfS-UWDM_lgOCOgY_Fn0XnIxKjZd3m_VkeG0QaWMSQCIWRJEQ--Ys'  # Client Secret real
PAYPAL_BASE_URL = 'https://api-m.sandbox.paypal.com'  # Cambia a https://api-m.paypal.com para producción

def get_paypal_access_token():
    """Obtener access token de PayPal"""
    url = f"{PAYPAL_BASE_URL}/v1/oauth2/token"
    headers = {
        'Accept': 'application/json',
        'Accept-Language': 'en_US',
    }
    data = {
        'grant_type': 'client_credentials'
    }
    response = requests.post(url, headers=headers, data=data, auth=(PAYPAL_CLIENT_ID, PAYPAL_CLIENT_SECRET))
    response.raise_for_status()
    return response.json()['access_token']

@app.route('/api/paypal/create-order', methods=['POST'])
def create_paypal_order():
    """Crear una orden de PayPal"""
    try:
        data = request.get_json()
        beat_name = data.get('beat_name', 'Beat')
        amount = f"{float(data.get('amount', '20.00')):.2f}"  # Formatear a dos decimales

        print(f"Creando orden PayPal: {beat_name} - ${amount}")

        access_token = get_paypal_access_token()
        print("Access token obtenido correctamente")

        url = f"{PAYPAL_BASE_URL}/v2/checkout/orders"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {access_token}'
        }

        order_data = {
            'intent': 'CAPTURE',
            'purchase_units': [{
                'amount': {
                    'currency_code': 'USD',
                    'value': amount
                },
                'description': f'Compra de beat: {beat_name}'
            }],
            'application_context': {
                'return_url': 'https://localhost:5000/success.html',
                'cancel_url': 'https://localhost:5000/checkout.html'
            }
        }

        print(f"Enviando orden a PayPal: {order_data}")
        response = requests.post(url, headers=headers, data=json.dumps(order_data))
        print(f"Respuesta PayPal: {response.status_code}")

        if response.status_code != 201:
            print(f"Error PayPal: {response.text}")
            return jsonify({'error': 'Error al procesar el pago con PayPal. Inténtalo de nuevo.'}), 500

        response.raise_for_status()
        order_response = response.json()
        print(f"Orden creada: {order_response.get('id')}")

        return jsonify(order_response)

    except requests.exceptions.RequestException as e:
        print(f"Request error: {str(e)}")
        return jsonify({'error': 'Error al procesar el pago con PayPal. Inténtalo de nuevo.'}), 500
    except Exception as e:
        print(f"General error: {str(e)}")
        return jsonify({'error': 'Error al procesar el pago con PayPal. Inténtalo de nuevo.'}), 500

@app.route('/api/paypal/capture-order/<order_id>', methods=['POST'])
def capture_paypal_order(order_id):
    """Capturar el pago de una orden de PayPal"""
    try:
        access_token = get_paypal_access_token()

        url = f"{PAYPAL_BASE_URL}/v2/checkout/orders/{order_id}/capture"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {access_token}'
        }

        response = requests.post(url, headers=headers)
        response.raise_for_status()

        return jsonify(response.json())

    except Exception as e:
        print(f"Error en captura: {str(e)}")
        return jsonify({'error': 'Error al procesar el pago con PayPal. Inténtalo de nuevo.'}), 500

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
    print("Servidor ejecutándose en http://localhost:5000")
    app.run(host='localhost', port=5000, debug=True)
