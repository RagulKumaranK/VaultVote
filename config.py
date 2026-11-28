import os

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

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

# Phone SMS Notification Configuration
SMS_ENABLED = os.environ.get('SMS_ENABLED', 'true').lower() in ('1', 'true', 'yes', 'on')
SMS_PROVIDER = os.environ.get('SMS_PROVIDER', 'simulation').strip().lower()  # simulation, twilio, fast2sms, webhook
SMS_COUNTRY_CODE = os.environ.get('SMS_COUNTRY_CODE', '+91').strip()
TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID', '').strip()
TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN', '').strip()
TWILIO_FROM_NUMBER = os.environ.get('TWILIO_FROM_NUMBER', '').strip()
FAST2SMS_API_KEY = os.environ.get('FAST2SMS_API_KEY', '').strip()
FAST2SMS_ROUTE = os.environ.get('FAST2SMS_ROUTE', 'q').strip()
SMS_WEBHOOK_URL = os.environ.get('SMS_WEBHOOK_URL', '').strip()
SMS_WEBHOOK_TOKEN = os.environ.get('SMS_WEBHOOK_TOKEN', '').strip()
