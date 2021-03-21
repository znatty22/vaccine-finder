import datetime
import os

# Data
ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
DEFAULT_INPUT_FILE = os.path.abspath(
    os.environ.get("VACCINE_FINDER_INPUT_FILE", None)
)

# Connections
REDIS_HOST = os.environ.get('REDIS_HOST', 'localhost')
REDIS_PORT = os.environ.get('REDIS_PORT', '6379')
TWILIO_ACCOUNT_ID = os.environ.get("TWILIO_ACCOUNT_ID")
TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.environ.get("TWILIO_PHONE_NUMBER")

# Jobs
WINDOW_START = datetime.time(6, 0, 0, 0)  # 6 am
WINDOW_END = datetime.time(23, 59, 0, 0)  # ~ 12 am
JOB_INTERVAL = int(os.environ.get('JOB_INTERVAL', 900))

# Finder
DEFAULT_PHONE_NUM = "+14846206937"
NOTIFY_VACCINE_USERS = bool(int(os.environ.get("NOTIFY_VACCINE_USERS", False)))
DEBUG_VACCINE_FINDER = bool(int(os.environ.get("DEBUG_VACCINE_FINDER", False)))
DEFAULT_ZIP_CODES = [19403]
DEFAULT_RADIUS = 50
