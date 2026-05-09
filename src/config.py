# Stores project settings such as storage path, admin IPs and passwords.

from datetime import timedelta

# External HDD storage location
UPLOAD_FOLDER = "/mnt/hdd"

# Admin devices with static IP addresses, mapping devices Ip's to friendly nicknames 
ADMIN_DEVICES = {
    "192.168.1.99": "FRARONNA HOME",   # FRARONNA computer
    "192.168.1.108": "TAGRGR LAPTOP",  # TAGRGR laptop
    "192.168.1.146": "TAGRGR PHONE"   # TAGRGR iPhone
}

# Password required for non-admin devices
ACCESS_PASSWORD = "123"

# Secret key used by Flask sessions
SECRET_KEY = "12345"

# Login session timeout
SESSION_LIFETIME = timedelta(minutes=30)

# Files/folders that should not appear or be modified
PROTECTED_ITEMS = ["System Volume Information"]

METADATA_FILE = "/mnt/hdd/metadata.json"

BIN_FOLDER = "/mnt/hdd/.bin"