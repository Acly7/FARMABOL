import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.environ.get('DB_PATH', os.path.join(BASE_DIR, 'farmabol.db'))
SECRET_KEY = os.environ.get('SECRET_KEY', 'farmabol-clave-local-cambiar-en-produccion')
PORT = int(os.environ.get('PORT', '8000'))
