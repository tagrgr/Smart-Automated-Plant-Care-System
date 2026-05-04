# Stores project settings such as storage path, admin IPs and passwords.

from datetime import timedelta

# External HDD storage location
UPLOAD_FOLDER = "/mnt/hdd"

# Admin devices with static IP addresses
ADMIN_IPS = [
    "192.168.1.99",   # FRARONNA computer
    "192.168.1.108",  # TAGRGR laptop
    "192.168.1.146"   # TAGRGR iPhone
]

# Password required for non-admin devices
ACCESS_PASSWORD = "123"

# Secret key used by Flask sessions
SECRET_KEY = "12345"

# Login session timeout
SESSION_LIFETIME = timedelta(minutes=30)

# Files/folders that should not appear or be modified
PROTECTED_ITEMS = ["System Volume Information"]