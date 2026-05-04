# Handles file-related helper functions for the cloud storage system.

import os
from datetime import datetime
from config import UPLOAD_FOLDER, PROTECTED_ITEMS


def get_visible_files():
    # Return only user files, hiding protected and hiden files
    return [
        f for f in os.listdir(UPLOAD_FOLDER)
        if f not in PROTECTED_ITEMS and not f.startswith(".")
    ]


def is_protected_file(filename):
    # Check if a file is protected or hidden
    return filename in PROTECTED_ITEMS or filename.startswith(".")


def get_file_path(filename):
    # Build the full file path inside the upload folder
    return os.path.join(UPLOAD_FOLDER, filename)


def get_file_info(filename):
    # Return useful information about a file
    file_path = get_file_path(filename)

    if not os.path.exists(file_path):
        return None

    file_size = os.path.getsize(file_path)
    file_size_mb = round(file_size / (1024 * 1024), 2)

    modified_time = os.path.getmtime(file_path)
    modified_date = datetime.fromtimestamp(modified_time).strftime("%d/%m/%Y %H:%M")

    return {
        "filename": filename,
        "size_mb": file_size_mb,
        "modified_date": modified_date,
        "location": UPLOAD_FOLDER
    }