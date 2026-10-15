import os

# Server Configuration
PORT = int(os.environ.get("PORT", 5000))
DEBUG = os.environ.get("FLASK_ENV", "development") == "development"

# Meta WhatsApp Cloud API Configuration
# Get these from Meta for Developers (developers.facebook.com) > WhatsApp > API Setup
WHATSAPP_CLOUD_TOKEN = os.environ.get("WHATSAPP_CLOUD_TOKEN", "")
PHONE_NUMBER_ID = os.environ.get("PHONE_NUMBER_ID", "")
VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN", "my_secret_whatsapp_verify_token_2026")

# Twilio WhatsApp Configuration
# Get these from Twilio Console (twilio.com/console)
TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN", "")
TWILIO_PHONE_NUMBER = os.environ.get("TWILIO_PHONE_NUMBER", "whatsapp:+14155238886")

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
UPLOADS_DIR = os.path.join(BASE_DIR, "uploads")

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(UPLOADS_DIR, exist_ok=True)
