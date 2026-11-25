import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

SECRET_KEY = os.environ.get('SECRET_KEY', 'vaultvote_super_secret_key_biometric_2026')
DB_PATH = os.path.join(BASE_DIR, 'vaultvote.db')

STATIC_DIR = os.path.join(BASE_DIR, 'static')
UPLOADS_DIR = os.path.join(STATIC_DIR, 'uploads')
FACES_DIR = os.path.join(UPLOADS_DIR, 'faces')
QRCODES_DIR = os.path.join(UPLOADS_DIR, 'qrcodes')
CARDS_DIR = os.path.join(UPLOADS_DIR, 'cards')

# Ensure directories exist
for directory in [UPLOADS_DIR, FACES_DIR, QRCODES_DIR, CARDS_DIR]:
    os.makedirs(directory, exist_ok=True)

# Voter ID sequence config
DEFAULT_VOTER_ID_PREFIX = 'WRM2745'
STARTING_SEQUENCE_NUMBER = 1

# Admin credentials default
DEFAULT_ADMIN_USERNAME = 'admin'
DEFAULT_ADMIN_PASSWORD = '123'
DEFAULT_ADMIN_NAME = 'Election Officer (Admin)'
