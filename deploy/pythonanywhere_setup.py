"""Configura Majestic Beats en PythonAnywhere (plan gratuito).

Uso, desde una consola Bash de PythonAnywhere, después de crear la web app
(Web -> Add a new web app -> Manual configuration):

    python3 ~/mejesticbeats/deploy/pythonanywhere_setup.py

Crea la carpeta privada de datos, genera las claves internas y escribe el
archivo WSGI de la web app. No toca el token de Mercado Pago: ese se pega a
mano en ~/majestic_data/secrets.py, que nunca sale de tu cuenta.
"""
import getpass
import os
import secrets
import stat

user = getpass.getuser()
home = os.path.expanduser('~')
project = os.path.join(home, 'mejesticbeats')
data_dir = os.path.join(home, 'majestic_data')
secrets_path = os.path.join(data_dir, 'secrets.py')
wsgi_path = f'/var/www/{user}_pythonanywhere_com_wsgi.py'

os.makedirs(os.path.join(data_dir, 'beats_privados'), exist_ok=True)
os.chmod(data_dir, stat.S_IRWXU)

if os.path.exists(secrets_path):
    print(f'Se conserva {secrets_path} (ya existía).')
    admin_token = None
else:
    admin_token = secrets.token_urlsafe(18)
    with open(secrets_path, 'w') as f:
        f.write(
            '# Claves de Majestic Beats. No compartas ni subas este archivo.\n'
            f'JWT_SECRET_KEY = {secrets.token_urlsafe(48)!r}\n'
            f'ADMIN_TOKEN = {admin_token!r}\n'
            "# Pega aquí tu Access Token de producción de Mercado Pago:\n"
            "MERCADO_PAGO_ACCESS_TOKEN = ''\n"
        )
    os.chmod(secrets_path, stat.S_IRUSR | stat.S_IWUSR)

wsgi = f'''# Generado por deploy/pythonanywhere_setup.py
import os
import sys
import importlib.util

DATA_DIR = {data_dir!r}
PROJECT = {project!r}

spec = importlib.util.spec_from_file_location('majestic_secrets', os.path.join(DATA_DIR, 'secrets.py'))
cfg = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cfg)

os.environ['DATA_DIR'] = DATA_DIR
for key in ('JWT_SECRET_KEY', 'ADMIN_TOKEN', 'MERCADO_PAGO_ACCESS_TOKEN'):
    value = getattr(cfg, key, '')
    if value:
        os.environ[key] = value

if PROJECT not in sys.path:
    sys.path.insert(0, PROJECT)
os.chdir(PROJECT)

from server import app as application  # noqa: E402
'''

try:
    with open(wsgi_path, 'w') as f:
        f.write(wsgi)
    print(f'Archivo WSGI escrito: {wsgi_path}')
except OSError as error:
    print(f'No se pudo escribir {wsgi_path}: {error}')
    print('Crea primero la web app en la pestaña Web y vuelve a ejecutar este script.')

print(f'Carpeta de datos: {data_dir}')
print(f'Tienda: https://{user}.pythonanywhere.com')
if admin_token:
    print(f'Clave del panel admin.html (guárdala): {admin_token}')
print(f'Falta: pegar el token de Mercado Pago en {secrets_path} y pulsar Reload en la pestaña Web.')
