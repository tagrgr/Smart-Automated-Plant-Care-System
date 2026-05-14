# Handles access control for admin devices and logged-in users.

import random
import string

from flask import request, session
from config import ADMIN_DEVICES

# this function checks out if user is admin and from there decide which home page user gets
def has_access():
    # Get the IP address of the device accessing the server
    user_ip = request.remote_addr

    # Admin devices can access without login
    if user_ip in ADMIN_DEVICES:
        return True

    # Other devices need an active login session
    return session.get("logged_in") == True


# This function returns the name of the current user/device
def get_current_user():
    # Get the IP address of the device accessing the server
    user_ip = request.remote_addr

    # If the IP belongs to an admin device, return the saved nickname
    if user_ip in ADMIN_DEVICES:
        return ADMIN_DEVICES[user_ip]

    # If visitor already has a name
    if "username" in session:
        return session["username"]

    # Otherwise generate one and store it
    guest_name = generate_guest_name()
    session["username"] = guest_name
    session.permanent = True
    return guest_name


def generate_guest_name():
    # 4 random characters (letters + numbers)
    random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    return f"Guest-{random_part}"


def get_current_avatar():
    if "avatar" in session:
        return session["avatar"]

    avatars = [
        "avatar1.jpg",
        "avatar2.jpg"
    ]

    avatar = random.choice(avatars)

    session["avatar"] = avatar
    session.permanent = True

    return avatar


def is_admin_device():
    user_ip = request.remote_addr
    return user_ip in ADMIN_DEVICES