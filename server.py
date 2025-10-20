from flask import Flask, send_from_directory, request, jsonify
import ssl
import os
import ipaddress
import requests
import json

app = Flask(__name__, static_folder='.')

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
    # Para desarrollo local con HTTPS y certificados de confianza
    import os
    import subprocess

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
        else:
            print("Sistema operativo no soportado para instalación automática de mkcert")
            exit(1)

        urllib.request.urlretrieve(url, filename)
        os.chmod(filename, 0o755)

    # Instalar CA de mkcert
    try:
        subprocess.run(['mkcert', '-install'], check=True)
        print("CA de mkcert instalado correctamente")
    except subprocess.CalledProcessError:
        print("Error instalando CA de mkcert")

    # Generar certificados para localhost
    cert_file = 'localhost.pem'
    key_file = 'localhost-key.pem'

    if not os.path.exists(cert_file) or not os.path.exists(key_file):
        try:
            subprocess.run(['mkcert', '-cert-file', cert_file, '-key-file', key_file, 'localhost', '127.0.0.1'], check=True)
            print("Certificados SSL generados correctamente")
        except subprocess.CalledProcessError:
            print("Error generando certificados SSL")

    # Ejecutar servidor HTTPS
    if os.path.exists(cert_file) and os.path.exists(key_file):
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(cert_file, key_file)

        print("Servidor HTTPS ejecutándose en https://localhost:5000")
        print("IMPORTANTE: Si ves advertencias de certificado, acepta el certificado de mkcert")
        print("Google OAuth funcionará correctamente con HTTPS")
        app.run(host='localhost', port=5000, ssl_context=context, debug=True)
    else:
        print("No se pudieron generar los certificados. Ejecutando en HTTP...")
        print("Servidor HTTP ejecutándose en http://localhost:5000")
        app.run(host='localhost', port=5000, debug=True)
