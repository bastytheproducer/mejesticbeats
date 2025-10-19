from flask import Flask, send_from_directory, request, jsonify
import ssl
import os
import ipaddress
import requests
import json

app = Flask(__name__, static_folder='.')

@app.route('/')
def index():
    return send_from_directory('.', 'login.html')

@app.route('/<path:filename>')
def serve_file(filename):
    return send_from_directory('.', filename)

@app.route('/api/auth/google', methods=['POST'])
def google_auth():
    data = request.get_json()
    # Simular validación de token de Google
    if data and 'credential' in data:
        return jsonify({'success': True, 'message': 'Autenticación exitosa'})
    return jsonify({'success': False, 'message': 'Token inválido'}), 400

# Configuración de PayPal (Sandbox)
PAYPAL_CLIENT_ID = 'TU_CLIENT_ID_SANDBOX'  # Reemplaza con tu Client ID real
PAYPAL_CLIENT_SECRET = 'TU_CLIENT_SECRET_SANDBOX'  # Reemplaza con tu Client Secret real
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
        amount = data.get('amount', '20.00')  # Monto por defecto

        access_token = get_paypal_access_token()

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

        response = requests.post(url, headers=headers, data=json.dumps(order_data))
        response.raise_for_status()

        return jsonify(response.json())

    except Exception as e:
        return jsonify({'error': str(e)}), 500

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
        return jsonify({'error': str(e)}), 500



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
