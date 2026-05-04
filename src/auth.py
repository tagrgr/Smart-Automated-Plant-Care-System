# Handles access control for admin devices and logged-in users.

from flask import request, session
from config import ADMIN_IPS

# this function will check out if user is admin and from there decide which home page user gets
def has_access():
    # Get the IP address of the device accessing the server
    user_ip = request.remote_addr

    # Admin devices can access without login
    if user_ip in ADMIN_IPS:
        return True

    # Other devices need an active login session
    return session.get("logged_in") == True