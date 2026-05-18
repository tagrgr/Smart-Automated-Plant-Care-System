# This creates a basic flask web server for the smart home pi, the server allows users to upload files and stores them in the project storage folder.
# Main app for our Home Server

import os
import json
import shutil

from flask import Flask, render_template, request, send_from_directory, redirect, session, flash

from datetime import datetime, timedelta

from config import (
    UPLOAD_FOLDER,
    BIN_FOLDER,
    BIN_METADATA_FILE,
    ACCESS_PASSWORD,
    SECRET_KEY,
    SESSION_LIFETIME,
    ADMIN_DEVICES
)

from auth import (
    has_access, 
    get_current_user, 
    get_current_avatar, 
    is_admin_device, 
    get_available_avatars
)

from file_manager import (
    get_visible_files,
    is_protected_file,
    get_file_path,
    add_file_metadata,
    get_file_metadata,
    load_metadata,
    save_metadata,
    get_bin_files,
    create_missing_metadata,
    is_folder,
    get_folders,
    get_folder_item_count
)

# Create flask application instance
app = Flask(__name__)


# test
@app.route("/test")
def test():
    return "TEST ROUTE WORKING"

@app.route("/public-test/<path:filename>")
def public_test(filename):
    file_path = get_file_path(filename)

    folder = os.path.dirname(file_path)
    base_name = os.path.basename(file_path)

    return send_from_directory(folder, base_name)


# Configure Flask session security and timeout
app.secret_key = SECRET_KEY
app.permanent_session_lifetime = SESSION_LIFETIME

# Make sure the upload and bin fodler exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(BIN_FOLDER, exist_ok=True)


def load_bin_metadata():
    if not os.path.exists(BIN_METADATA_FILE):
        return {}

    with open(BIN_METADATA_FILE, "r") as file:
        return json.load(file)


def save_bin_metadata(metadata):
    with open(BIN_METADATA_FILE, "w") as file:
        json.dump(metadata, file, indent=4)


def cleanup_old_bin_files():
    bin_metadata = load_bin_metadata()
    updated_metadata = {}

    for filename, data in bin_metadata.items():
        deleted_at = datetime.strptime(data["deleted_at"], "%Y-%m-%d %H:%M:%S")
        expiry_date = deleted_at + timedelta(days=30)

        bin_path = os.path.join(BIN_FOLDER, filename)

        if datetime.now() > expiry_date:
            if os.path.exists(bin_path):
                if os.path.isdir(bin_path):
                    shutil.rmtree(bin_path)
                else:
                    os.remove(bin_path)
        else:
            updated_metadata[filename] = data

    save_bin_metadata(updated_metadata)


def redirect_back(default="/"):
    return redirect(request.referrer or default)


def is_image_file(filename):
    image_extensions = [
        ".png", ".jpg", ".jpeg", ".gif", ".webp"
    ]
    extension = os.path.splitext(filename)[1].lower()

    return extension in image_extensions


def get_file_icon(filename):
    extension = os.path.splitext(filename)[1].lower()

    icons = {
        ".pdf": "📕",

        ".zip": "🗜", ".rar": "🗜", ".7z": "🗜",

        ".mp4": "🎥", ".mov": "🎥", ".avi": "🎥",

        ".mp3": "🎵", ".wav": "🎵",

        ".xlsx": "📊", ".xls": "📊", ".csv": "📊",

        ".txt": "📝",

        ".py": "💻", ".js": "💻", ".html": "💻", ".css": "💻", ".json": "💻",

        ".docx": "📘", ".doc": "📘"
    }

    return icons.get(extension, "📄")


def get_storage_info():
    total, used, _ = shutil.disk_usage(UPLOAD_FOLDER)

    total_gb = round(total / (1024 ** 3), 2)
    used_gb = round(used / (1024 ** 3), 2)
    percent_used = round((used / total) * 100)

    return {
        "total_gb": total_gb,
        "used_gb": used_gb,
        "percent_used": percent_used
    }


def is_video_file(filename):
    video_extensions = [".mp4", ".mov", ".avi", ".webm"]
    extension = os.path.splitext(filename)[1].lower()
    
    return extension in video_extensions


def serve_file(filename, download=False):
    if not has_access():
        return "Unauthorized", 401

    if is_protected_file(filename):
        return "Action not allowed"

    file_path = get_file_path(filename)

    if not os.path.exists(file_path):
        return "File not found"

    folder = os.path.dirname(file_path)
    base_name = os.path.basename(file_path)

    return send_from_directory(
        folder,
        base_name,
        as_attachment=download
    )


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        password = request.form.get("password")

        if password == ACCESS_PASSWORD:
            # Keep the login active for the session timeout period
            session.permanent = True
            session["logged_in"] = True
            return redirect("/")

        return "Incorrect password <br><a href='/login'>Try again</a>"

    return render_template("login.html")


@app.route("/test")
def test():
    return "TEST WORKING"


# Define route for homepage
@app.route("/")
def home():
    if not has_access():
        return redirect("/login")

    current_user = get_current_user()
    create_missing_metadata(current_user)

    # Get list of files from storage and hide System Volume Information directory  and hidden system files as they're useless for our project
    files = []
    for filename in get_visible_files():
        metadata = get_file_metadata(filename)

        files.append({
            "name": filename,
            "full_path": filename,
            "owner": metadata["owner"],
            "visibility": metadata["visibility"],
            "location": metadata["location"],
            "is_folder": is_folder(filename),
            "is_image": is_image_file(filename),
            "is_video": is_video_file(filename),
            "file_icon": get_file_icon(filename),
            "modified_time": os.path.getmtime(get_file_path(filename)),
            "item_count": get_folder_item_count(filename) if is_folder(filename) else 0,
        })

    return render_template(
        "home.html",
        current_user=current_user,
        files=files,
        folders=get_folders(),
        current_page="home",
        breadcrumbs=[],
        current_folder="",
        storage=get_storage_info(),
        current_avatar=get_current_avatar(),
        avatars=get_available_avatars(),
        is_admin=is_admin_device(),
        open_profile_modal=request.args.get("profile") == "open"
    )


# my drive route
@app.route("/my-drive")
def my_drive():
    if not has_access():
        return redirect("/login")

    current_user = get_current_user()
    files = []

    for filename in get_visible_files():
        metadata = get_file_metadata(filename)

        if (
            metadata["owner"] == current_user and
            metadata["visibility"] == "private"
        ):
            files.append({
                "name": filename,
                "full_path": filename,
                "owner": metadata["owner"],
                "visibility": metadata["visibility"],
                "location": metadata["location"],
                "is_folder": is_folder(filename),
                "is_image": is_image_file(filename),
                "is_video": is_video_file(filename),
                "file_icon": get_file_icon(filename),
                "modified_time": os.path.getmtime(get_file_path(filename)),
                "item_count": get_folder_item_count(filename) if is_folder(filename) else 0,
            })

    return render_template(
        "home.html",
        current_user=current_user,
        files=files,
        folders=get_folders(),
        current_page="my-drive",
        storage=get_storage_info(),
        current_avatar=get_current_avatar(),
        avatars=get_available_avatars(),
        is_admin=is_admin_device(),
        open_profile_modal=request.args.get("profile") == "open"
    )


# shared with me route
@app.route("/shared")
def shared_files():
    if not has_access():
        return redirect("/login")

    current_user = get_current_user()
    files = []

    for filename in get_visible_files():
        metadata = get_file_metadata(filename)

        if (
            metadata["visibility"] == "shared" and
            metadata["owner"] != current_user
        ):
            files.append({
                "name": filename,
                "full_path": filename,
                "owner": metadata["owner"],
                "visibility": metadata["visibility"],
                "location": metadata["location"],
                "is_folder": is_folder(filename),
                "is_image": is_image_file(filename),
                "is_video": is_video_file(filename),
                "file_icon": get_file_icon(filename),
                "modified_time": os.path.getmtime(get_file_path(filename)),
                "item_count": get_folder_item_count(filename) if is_folder(filename) else 0,
            })

    return render_template(
        "home.html",
        current_user=current_user,
        files=files,
        folders=get_folders(),
        current_page="shared",
        storage=get_storage_info(),
        current_avatar=get_current_avatar(),
        avatars=get_available_avatars(),
        is_admin=is_admin_device(),
        open_profile_modal=request.args.get("profile") == "open"
    )


# Upload route
@app.route("/upload", methods=["POST"])
def upload_file():
    if not has_access():
        return redirect("/login")

    uploaded_files = request.files.getlist("files")
    visibility = request.form.get("visibility", "private")
    current_folder = request.form.get("current_folder", "")

    # Check if the request contains a file
    if not uploaded_files or uploaded_files[0].filename == "":
        flash("No file selected", "error")
        return redirect_back()

    if len(uploaded_files) > 30:
        flash("You can upload a maximum of 30 files at a time", "error")
        return redirect_back()

    uploaded_count = 0

    # Check if the file has a name
    for file in uploaded_files:
        if file.filename == "":
            continue

        relative_path = os.path.join(current_folder, file.filename) if current_folder else file.filename
        save_path = get_file_path(relative_path)
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        file.save(save_path)
        add_file_metadata(relative_path, get_current_user(), visibility)
        uploaded_count += 1

    flash(f"{uploaded_count} file(s) uploaded as {visibility}", "success")
    return redirect_back()


@app.route("/download/<path:filename>")
def download_file(filename):
    return serve_file(filename, download=True)


@app.route("/view/<path:filename>")
def view_file(filename):
    return serve_file(filename)



# delete route
@app.route("/delete/<path:filename>", methods=["POST"])
def delete_file(filename):
    if not has_access():
        return redirect("/login")

    # Prevent deleting protected or hidden files
    if is_protected_file(filename):
        flash("Action not allowed", "error")
        return redirect_back()

    file_path = get_file_path(filename)

    if os.path.exists(file_path):
        base_name = os.path.basename(filename)

        bin_path = os.path.join(BIN_FOLDER, base_name)
        counter = 1
        name, extension = os.path.splitext(base_name)

        while os.path.exists(bin_path):
            new_filename = f"{name}_deleted_{counter}{extension}"
            bin_path = os.path.join(BIN_FOLDER, new_filename)
            counter += 1

        shutil.move(file_path, bin_path)

        bin_filename = os.path.basename(bin_path)
        bin_metadata = load_bin_metadata()
        bin_metadata[bin_filename] = {
            "deleted_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        save_bin_metadata(bin_metadata)

        # Remove file from normal metadata after moving to Bin
        metadata = load_metadata()
        if filename in metadata:
            metadata.pop(filename)
            save_metadata(metadata)

        flash(f"'{base_name}' moved to Bin", "success")
    else:
        flash("File not found", "error")

    return redirect_back()


@app.route("/copy/<path:filename>", methods=["POST"])
def copy_file(filename):
    if not has_access():
        return redirect("/login")

    if is_protected_file(filename):
        flash("Action not allowed", "error")
        return redirect_back()

    original_path = get_file_path(filename)

    if not os.path.exists(original_path):
        flash("File not found", "error")
        return redirect_back()

    folder = os.path.dirname(filename)
    base_name = os.path.basename(filename)

    name, extension = os.path.splitext(base_name)
    copied_filename = f"{name}_copy{extension}"

    copied_relative_path = (
        os.path.join(folder, copied_filename)
        if folder else copied_filename
    )

    copied_path = get_file_path(copied_relative_path)

    counter = 1
    while os.path.exists(copied_path):
        copied_filename = f"{name}_copy_{counter}{extension}"

        copied_relative_path = (
            os.path.join(folder, copied_filename)
            if folder else copied_filename
        )

        copied_path = get_file_path(copied_relative_path)
        counter += 1

    if os.path.isdir(original_path):
        shutil.copytree(original_path, copied_path)
    else:
        shutil.copy2(original_path, copied_path)

    # Copy metadata too
    metadata = get_file_metadata(filename)

    add_file_metadata(
        copied_relative_path,
        metadata["owner"],
        metadata["visibility"]
    )

    flash(f"File copied as '{copied_filename}'", "success")

    return redirect_back()


@app.route("/toggle-visibility/<path:filename>", methods=["POST"])
def toggle_visibility(filename):
    if not has_access():
        return redirect("/login")

    if is_protected_file(filename):
        flash("Action not allowed", "error")
        return redirect_back()

    metadata = load_metadata()

    if filename not in metadata:
        flash("File metadata not found", "error")
        return redirect_back()

    current_visibility = metadata[filename]["visibility"]

    if current_visibility == "private":
        metadata[filename]["visibility"] = "shared"
        flash(f"'{os.path.basename(filename)}' is now shared", "success")
    else:
        metadata[filename]["visibility"] = "private"
        flash(f"'{os.path.basename(filename)}' is now private", "success")

    save_metadata(metadata)

    return redirect_back()

# bin page route
@app.route("/bin")
def bin_page():
    if not has_access():
        return redirect("/login")

    current_user = get_current_user()
    files = []
    bin_metadata = load_bin_metadata()

    for filename in get_bin_files():
        deleted_data = bin_metadata.get(filename)

        days_remaining = "Unknown"

        if deleted_data:
            deleted_at = datetime.strptime(
                deleted_data["deleted_at"],
                "%Y-%m-%d %H:%M:%S"
            )

            expiry_date = deleted_at + timedelta(days=30)
            remaining = expiry_date - datetime.now()
            days_remaining = max(0, remaining.days)

        files.append({
            "name": filename,
            "full_path": filename,
            "owner": "Deleted",
            "visibility": "bin",
            "location": f"Deletes in {days_remaining} days",
            "is_folder": os.path.isdir(os.path.join(BIN_FOLDER, filename)),
            "is_image": is_image_file(filename),
            "is_video": is_video_file(filename),
            "file_icon": get_file_icon(filename),
            "modified_time": os.path.getmtime(os.path.join(BIN_FOLDER, filename)),
            # "item_count": get_folder_item_count(filename) if is_folder(filename) else 0,
            "item_count": 0,
        })

    return render_template(
        "home.html",
        current_user=current_user,
        files=files,
        folders=get_folders(),
        current_page="bin",
        storage=get_storage_info(),
        current_avatar=get_current_avatar(),
        avatars=get_available_avatars(),
        is_admin=is_admin_device(),
        open_profile_modal=request.args.get("profile") == "open",
    )


@app.route("/restore/<path:filename>", methods=["POST"])
def restore_file(filename):
    if not has_access():
        return redirect("/login")

    bin_path = os.path.join(BIN_FOLDER, filename)
    base_name = os.path.basename(filename)
    restore_path = get_file_path(base_name)

    if not os.path.exists(bin_path):
        flash("File not found in Bin", "error")
        return redirect("/bin")

    counter = 1
    name, extension = os.path.splitext(base_name)

    while os.path.exists(restore_path):
        restored_filename = f"{name}_restored_{counter}{extension}"
        restore_path = get_file_path(restored_filename)
        counter += 1

    shutil.move(bin_path, restore_path)

    # Remove restored file from Bin metadata
    bin_metadata = load_bin_metadata()
    if filename in bin_metadata:
        bin_metadata.pop(filename)
        save_bin_metadata(bin_metadata)

    # Add normal metadata again
    restored_filename = os.path.basename(restore_path)
    add_file_metadata(restored_filename, get_current_user(), "private")

    flash(f"File '{restored_filename}' restored successfully", "success")
    return redirect("/bin")


@app.route("/delete-permanently/<path:filename>", methods=["POST"])
def delete_permanently(filename):
    if not has_access():
        return redirect("/login")

    bin_path = os.path.join(BIN_FOLDER, filename)

    if not os.path.exists(bin_path):
        flash("File not found in Bin", "error")
        return redirect("/bin")

    # Delete file or folder
    if os.path.isdir(bin_path):
        shutil.rmtree(bin_path)
    else:
        os.remove(bin_path)

    # Remove Bin metadata
    bin_metadata = load_bin_metadata()

    if filename in bin_metadata:
        bin_metadata.pop(filename)
        save_bin_metadata(bin_metadata)

    flash(f"'{os.path.basename(filename)}' permanently deleted", "success")

    return redirect("/bin")


@app.route("/create-folder", methods=["POST"])
def create_new_folder():
    if not has_access():
        return redirect("/login")

    folder_name = request.form.get("folder_name", "").strip()
    current_folder = request.form.get("current_folder", "")

    if not folder_name:
        flash("Folder name is required", "error")
        return redirect_back()

    relative_path = os.path.join(current_folder, folder_name) if current_folder else folder_name
    folder_path = get_file_path(relative_path)

    if os.path.exists(folder_path):
        flash("A folder with this name already exists", "error")
        return redirect_back()

    os.makedirs(folder_path)
    add_file_metadata(relative_path, get_current_user(), "private")

    flash(f"Folder '{folder_name}' created successfully", "success")

    return redirect_back()


@app.route("/folder/<path:folder_name>")
def open_folder(folder_name):
    if not has_access():
        return redirect("/login")

    current_user = get_current_user()
    breadcrumbs = []
    parts = folder_name.split("/")
    current_path = ""

    for part in parts:
        current_path = os.path.join(current_path, part)
        breadcrumbs.append({
            "name": part,
            "path": current_path
        })

    folder_path = get_file_path(folder_name)

    if not os.path.isdir(folder_path):
        flash("Folder not found", "error")
        return redirect_back()

    files = []

    for filename in get_visible_files(folder_path):
        full_relative_path = os.path.join(folder_name, filename)
        metadata = get_file_metadata(full_relative_path)

        files.append({
            "name": filename,
            "full_path": full_relative_path,
            "owner": metadata["owner"],
            "visibility": metadata["visibility"],
            "location": folder_name,
            "is_folder": is_folder(full_relative_path),
            "is_image": is_image_file(filename),
            "is_video": is_video_file(filename),
            "file_icon": get_file_icon(filename),
            "modified_time": os.path.getmtime(get_file_path(full_relative_path)),
            "item_count": get_folder_item_count(full_relative_path) if is_folder(full_relative_path) else 0,
        })

    return render_template(
        "home.html",
        current_user=current_user,
        files=files,
        folders=get_folders(),
        current_page="home",
        current_folder=folder_name,
        breadcrumbs=breadcrumbs,
        storage=get_storage_info(),
        current_avatar=get_current_avatar(),
        avatars=get_available_avatars(),
        is_admin=is_admin_device(),
        open_profile_modal=request.args.get("profile") == "open"        
    )


@app.route("/bulk-bin", methods=["POST"])
def bulk_move_to_bin():
    if not has_access():
        return redirect("/login")

    selected_files = request.form.getlist("selected_files")

    if not selected_files:
        flash("No files selected", "error")
        return redirect_back()

    moved_count = 0
    metadata = load_metadata()
    bin_metadata = load_bin_metadata()

    for filename in selected_files:
        if is_protected_file(filename):
            continue

        file_path = get_file_path(filename)

        if os.path.exists(file_path):
            base_name = os.path.basename(filename)
            bin_path = os.path.join(BIN_FOLDER, base_name)
            counter = 1
            name, extension = os.path.splitext(base_name)

            while os.path.exists(bin_path):
                new_filename = f"{name}_deleted_{counter}{extension}"
                bin_path = os.path.join(BIN_FOLDER, new_filename)
                counter += 1

            shutil.move(file_path, bin_path)

            bin_filename = os.path.basename(bin_path)

            bin_metadata[bin_filename] = {
                "deleted_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }

            if filename in metadata:
                metadata.pop(filename)

            moved_count += 1

    save_metadata(metadata)
    save_bin_metadata(bin_metadata)

    flash(f"{moved_count} item(s) moved to Bin", "success")
    return redirect_back()


@app.route("/bulk-copy", methods=["POST"])
def bulk_copy_files():
    if not has_access():
        return redirect("/login")

    selected_files = request.form.getlist("selected_files")

    if not selected_files:
        flash("No files selected", "error")
        return redirect_back()

    copied_count = 0

    for filename in selected_files:
        original_path = get_file_path(filename)

        if not os.path.exists(original_path):
            continue

        folder = os.path.dirname(filename)
        base_name = os.path.basename(filename)
        name, extension = os.path.splitext(base_name)

        copied_filename = f"{name}_copy{extension}"
        copied_relative_path = os.path.join(folder, copied_filename) if folder else copied_filename
        copied_path = get_file_path(copied_relative_path)

        counter = 1
        while os.path.exists(copied_path):
            copied_filename = f"{name}_copy_{counter}{extension}"
            copied_relative_path = os.path.join(folder, copied_filename) if folder else copied_filename
            copied_path = get_file_path(copied_relative_path)
            counter += 1

        if os.path.isdir(original_path):
            shutil.copytree(original_path, copied_path)
        else:
            shutil.copy2(original_path, copied_path)

        metadata = get_file_metadata(filename)
        add_file_metadata(
            copied_relative_path,
            metadata["owner"],
            metadata["visibility"]
        )

        copied_count += 1

    flash(f"{copied_count} file(s) copied successfully", "success")
    return redirect_back()


@app.route("/bulk-toggle-visibility", methods=["POST"])
def bulk_toggle_visibility():
    if not has_access():
        return redirect("/login")

    selected_files = request.form.getlist("selected_files")

    if not selected_files:
        flash("No files selected", "error")
        return redirect_back()

    metadata = load_metadata()
    changed_count = 0

    for filename in selected_files:
        if filename in metadata:
            if metadata[filename]["visibility"] == "private":
                metadata[filename]["visibility"] = "shared"
            else:
                metadata[filename]["visibility"] = "private"

            changed_count += 1

    save_metadata(metadata)

    flash(f"Visibility changed for {changed_count} item(s)", "success")
    return redirect_back()


@app.route("/rename/<path:filename>", methods=["POST"])
def rename_file(filename):
    if not has_access():
        return redirect("/login")

    new_name = request.form.get("new_name", "").strip()

    if not new_name:
        flash("New name is required", "error")
        return redirect_back()

    old_path = get_file_path(filename)
    folder = os.path.dirname(filename)
    new_relative_path = os.path.join(folder, new_name) if folder else new_name
    new_path = get_file_path(new_relative_path)

    if not os.path.exists(old_path):
        flash("File not found", "error")
        return redirect_back()

    if os.path.exists(new_path):
        flash("A file with this name already exists", "error")
        return redirect_back()

    os.rename(old_path, new_path)
    metadata = load_metadata()

    if filename in metadata:
        metadata[new_relative_path] = metadata.pop(filename)
        metadata[new_relative_path]["location"] = folder if folder else "/"

    save_metadata(metadata)
    flash(f"Renamed to '{new_name}'", "success")

    if folder:
        return redirect(f"/folder/{folder}")

    return redirect("/")


@app.route("/bulk-move", methods=["POST"])
def bulk_move():
    if not has_access():
        return redirect("/login")

    selected_files = request.form.getlist("selected_files")
    destination = request.form.get("destination")
    return_to = request.form.get("return_to", "/")

    if not selected_files:
        flash("No files selected", "error")
        return redirect(return_to)

    moved_count = 0
    metadata = load_metadata()

    for filename in selected_files:
        source_path = get_file_path(filename)

        if not os.path.exists(source_path):
            continue

        base_name = os.path.basename(filename)

        if destination == "":
            new_relative_path = base_name
            new_location = "/"
        else:
            new_relative_path = os.path.join(destination, base_name)
            new_location = destination

        destination_path = get_file_path(new_relative_path)
        counter = 1
        name, extension = os.path.splitext(base_name)

        while os.path.exists(destination_path):
            new_name = f"{name}_moved_{counter}{extension}"
            new_relative_path = os.path.join(destination, new_name) if destination else new_name
            destination_path = get_file_path(new_relative_path)
            counter += 1

        shutil.move(source_path, destination_path)

        if filename in metadata:
            metadata[new_relative_path] = metadata.pop(filename)
            metadata[new_relative_path]["location"] = new_location

        moved_count += 1

    save_metadata(metadata)

    flash(f"{moved_count} item(s) moved successfully", "success")
    return redirect(return_to)


@app.route("/set-theme", methods=["POST"])
def set_theme():
    if not has_access():
        return redirect("/login")

    selected_theme = request.form.get("theme", "light")
    session["theme"] = selected_theme

    flash(f"{selected_theme.capitalize()} mode enabled", "success")
    return redirect((request.referrer or "/") + "?profile=open")


@app.route("/set-avatar", methods=["POST"])
def set_avatar():
    if not has_access():
        return redirect("/login")

    selected_avatar = request.form.get("avatar")
    allowed_avatars = get_available_avatars()

    if selected_avatar in allowed_avatars:
        session["avatar"] = selected_avatar
        flash("Avatar updated successfully", "success")

    return redirect((request.referrer or "/") + "?profile=open")


@app.route("/set-nickname", methods=["POST"])
def set_nickname():
    if not has_access():
        return redirect("/login")

    if not is_admin_device():
        flash("Only admin devices can change nicknames", "error")
        return redirect_back()

    new_nickname = request.form.get("nickname", "").strip()

    if not new_nickname:
        flash("Nickname cannot be empty", "error")
        return redirect_back()

    user_ip = request.remote_addr
    ADMIN_DEVICES[user_ip] = new_nickname

    flash("Nickname updated successfully", "success")
    return redirect((request.referrer or "/") + "?profile=open")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


@app.route("/my-ip")
def my_ip():
    return f"Your IP is: {request.remote_addr}"


cleanup_old_bin_files()

# Run the Flask app
if __name__ == "__main__":
    # host="0.0.0.0" allows other devices on the WiFi network to access the app
    app.run(host="0.0.0.0", port=5000)