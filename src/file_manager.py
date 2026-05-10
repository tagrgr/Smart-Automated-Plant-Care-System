# Handles file-related helper functions for the cloud storage system.

import os
import json

from datetime import datetime
from config import UPLOAD_FOLDER, PROTECTED_ITEMS, METADATA_FILE, BIN_FOLDER


def get_visible_files(folder_path=UPLOAD_FOLDER):
    # Return only user files, hiding protected and hiden files
    return [
        f for f in os.listdir(folder_path)
        if f not in PROTECTED_ITEMS and not f.startswith(".")
    ]


def is_protected_file(filename):
    # Check if a file is protected or hidden
    return filename in PROTECTED_ITEMS or filename.startswith(".")


def get_file_path(filename, current_path=""):
    # Build the full file path inside the upload folder
    return os.path.join(UPLOAD_FOLDER, current_path, filename)


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


def load_metadata():
    if not os.path.exists(METADATA_FILE):
        return {}

    with open(METADATA_FILE, "r") as file:
        return json.load(file)


def save_metadata(metadata):
    with open(METADATA_FILE, "w") as file:
        json.dump(metadata, file, indent=4)


def add_file_metadata(filename, owner, visibility):
    metadata = load_metadata()

    metadata[filename] = {
        "owner": owner,
        "visibility": visibility,
        "location": "/"
    }

    save_metadata(metadata)


def get_file_metadata(filename):
    metadata = load_metadata()

    return metadata.get(filename, {
        "owner": "Unknown",
        "visibility": "private",
        "location": "/"
    })


def get_bin_files():
    if not os.path.exists(BIN_FOLDER):
        return []

    return [
        f for f in os.listdir(BIN_FOLDER)
        if not f.startswith(".")
    ]


def create_missing_metadata(owner):
    metadata = load_metadata()

    for filename in get_visible_files():
        if filename not in metadata:
            metadata[filename] = {
                "owner": owner,
                "visibility": "private",
                "location": "/"
            }

    save_metadata(metadata)


def create_folder(folder_name):
    folder_path = os.path.join(UPLOAD_FOLDER, folder_name)

    if os.path.exists(folder_path):
        return False

    os.makedirs(folder_path)
    return True


def is_folder(filename):
    return os.path.isdir(get_file_path(filename))


def get_folders():
    return [
        item for item in os.listdir(UPLOAD_FOLDER)
        if os.path.isdir(os.path.join(UPLOAD_FOLDER, item))
        and item not in PROTECTED_ITEMS
        and not item.startswith(".")
    ]