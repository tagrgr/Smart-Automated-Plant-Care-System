# This creates a basic flask web server for the smart home pi, the server allows users to upload files and stores them in the project storage folder.
# Main app for our Home Server

import os
import json
import shutil

from flask import Flask, render_template, request, send_from_directory, redirect, url_for, session, flash

from datetime import datetime, timedelta

from config import (
    UPLOAD_FOLDER,
    BIN_FOLDER,
    BIN_METADATA_FILE,
    ACCESS_PASSWORD,
    SECRET_KEY,
    SESSION_LIFETIME
)

from auth import has_access, get_current_user
from file_manager import (
    get_visible_files,
    is_protected_file,
    get_file_path,
    get_file_info,
    add_file_metadata,
    get_file_metadata,
    load_metadata,
    save_metadata,
    get_bin_files,
    create_missing_metadata,
    create_folder,
    is_folder,
    get_folders
)

# Create flask application instance
app = Flask(__name__)

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
                os.remove(bin_path)
        else:
            updated_metadata[filename] = data

    save_bin_metadata(updated_metadata)


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
            "is_folder": is_folder(filename)
        })

    return render_template(
        "home.html",
        current_user=current_user,
        files=files,
        current_page="home"
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
                "is_folder": is_folder(filename)
            })

    return render_template(
        "home.html",
        current_user=current_user,
        files=files,
        current_page="my-drive"
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
                "is_folder": is_folder(filename)
            })

    return render_template(
        "home.html",
        current_user=current_user,
        files=files,
        current_page="shared"
    )


# Upload route
@app.route("/upload", methods=["POST"])
def upload_file():
    if not has_access():
        return redirect("/login")

    uploaded_files = request.files.getlist("files")
    visibility = request.form.get("visibility", "private")

    # Check if the request contains a file
    if not uploaded_files or uploaded_files[0].filename == "":
        flash("No file selected", "error")
        return redirect("/")

    if len(uploaded_files) > 30:
        flash("You can upload a maximum of 30 files at a time", "error")
        return redirect("/")

    uploaded_count = 0

    # Check if the file has a name
    for file in uploaded_files:
        if file.filename == "":
            continue

        # Create the full save path inside the storage folder
        save_path = get_file_path(file.filename)
        # Save the uploaded file to the Raspberry Pi
        file.save(save_path)
        add_file_metadata(file.filename, get_current_user(), visibility)
        uploaded_count += 1

    flash(f"{uploaded_count} file(s) uploaded as {visibility}", "success")
    return redirect("/")


# download route
@app.route("/download/<filename>")
def download_file(filename):
    if not has_access():
        return redirect("/login")
    
    if is_protected_file(filename):
        return "Action not allowed"
            
    return send_from_directory(UPLOAD_FOLDER, filename, as_attachment=True)


@app.route("/info/<filename>")
def file_info(filename):
    if not has_access():
        return redirect("/login")

    # Prevent access to protected or hidden files
    if is_protected_file(filename):
        return "Action not allowed"

    info = get_file_info(filename)

    # Check if file exists before showing information
    if info is None:
        return "File not found"

    return render_template("file_info.html", info=info)


@app.route("/confirm-delete/<filename>")
def confirm_delete(filename):
    if not has_access():
        return redirect("/login")

    # Prevent system/hidden files
    if is_protected_file(filename):
        return "Action not allowed"

    return render_template("confirm_delete.html", filename=filename)


# delete route
@app.route("/delete/<filename>", methods=["POST"])
def delete_file(filename):
    if not has_access():
        return redirect("/login")
    
    # Prevent deleting protected or hidden files
    if is_protected_file(filename):
        flash("Action not allowed", "error")
        return "Action not allowed"

    # Create the full path to the selected file
    file_path = get_file_path(filename)

    # Check if the file exists before trying to delete it
    if os.path.exists(file_path):
        bin_path = os.path.join(BIN_FOLDER, filename)

        counter = 1
        name, extension = os.path.splitext(filename)

        while os.path.exists(bin_path):
            new_filename = f"{name}_deleted_{counter}{extension}"
            bin_path = os.path.join(BIN_FOLDER, new_filename)
            counter += 1

        shutil.move(file_path, bin_path)

        bin_metadata = load_bin_metadata()
        bin_metadata[os.path.basename(bin_path)] = {
            "deleted_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        save_bin_metadata(bin_metadata)

        flash(f"File '{filename}' moved to Bin", "success")
    else:
        flash("File not found", "error")

    # Send the user back to the home page after deleting
    return redirect("/")


@app.route("/copy/<filename>", methods=["POST"])
def copy_file(filename):
    if not has_access():
        return redirect("/login")

    if is_protected_file(filename):
        flash("Action not allowed", "error")
        return redirect("/")

    original_path = get_file_path(filename)

    if not os.path.exists(original_path):
        flash("File not found", "error")
        return redirect("/")

    name, extension = os.path.splitext(filename)
    copied_filename = f"{name}_copy{extension}"
    copied_path = get_file_path(copied_filename)

    counter = 1
    while os.path.exists(copied_path):
        copied_filename = f"{name}_copy_{counter}{extension}"
        copied_path = get_file_path(copied_filename)
        counter += 1

    shutil.copy2(original_path, copied_path)

    flash(f"File copied as '{copied_filename}'", "success")
    return redirect("/")


@app.route("/toggle-visibility/<filename>", methods=["POST"])
def toggle_visibility(filename):
    if not has_access():
        return redirect("/login")

    if is_protected_file(filename):
        flash("Action not allowed", "error")
        return redirect("/")

    metadata = load_metadata()

    if filename not in metadata:
        flash("File metadata not found", "error")
        return redirect("/")

    current_visibility = metadata[filename]["visibility"]

    if current_visibility == "private":
        metadata[filename]["visibility"] = "shared"
        flash(f"'{filename}' is now shared", "success")
    else:
        metadata[filename]["visibility"] = "private"
        flash(f"'{filename}' is now private", "success")

    save_metadata(metadata)

    return redirect("/")

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
            "is_folder": is_folder(filename)
        })

    return render_template(
        "home.html",
        current_user=current_user,
        files=files,
        current_page="bin"
    )


@app.route("/restore/<filename>", methods=["POST"])
def restore_file(filename):
    if not has_access():
        return redirect("/login")

    bin_path = os.path.join(BIN_FOLDER, filename)
    restore_path = get_file_path(filename)

    if not os.path.exists(bin_path):
        flash("File not found in Bin", "error")
        return redirect("/bin")

    counter = 1
    name, extension = os.path.splitext(filename)

    while os.path.exists(restore_path):
        restored_filename = f"{name}_restored_{counter}{extension}"
        restore_path = get_file_path(restored_filename)
        counter += 1

    shutil.move(bin_path, restore_path)

    flash(f"File '{filename}' restored successfully", "success")
    return redirect("/bin")


@app.route("/delete-permanently/<filename>", methods=["POST"])
def delete_permanently(filename):
    if not has_access():
        return redirect("/login")

    bin_path = os.path.join(BIN_FOLDER, filename)

    if not os.path.exists(bin_path):
        flash("File not found in Bin", "error")
        return redirect("/bin")

    os.remove(bin_path)

    flash(f"File '{filename}' permanently deleted", "success")
    return redirect("/bin")


@app.route("/create-folder", methods=["POST"])
def create_new_folder():
    if not has_access():
        return redirect("/login")

    folder_name = request.form.get("folder_name")

    if not folder_name:
        flash("Folder name is required", "error")
        return redirect("/")

    if create_folder(folder_name):
        add_file_metadata(folder_name, get_current_user(), "private")
        flash(f"Folder '{folder_name}' created successfully", "success")
    else:
        flash("A folder with this name already exists", "error")

    return redirect("/")


@app.route("/folder/<path:folder_name>")
def open_folder(folder_name):
    if not has_access():
        return redirect("/login")

    current_user = get_current_user()

    folder_path = get_file_path(folder_name)

    if not os.path.isdir(folder_path):
        flash("Folder not found", "error")
        return redirect("/")

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
            "is_folder": is_folder(full_relative_path)
        })

    return render_template(
        "home.html",
        current_user=current_user,
        files=files,
        current_page="home",
        current_folder=folder_name
    )


@app.route("/move-page/<path:filename>")
def move_page(filename):
    if not has_access():
        return redirect("/login")

    folders = get_folders()

    return render_template(
        "move_file.html",
        filename=filename,
        folders=folders
    )


@app.route("/move/<path:filename>", methods=["POST"])
def move_file(filename):
    if not has_access():
        return redirect("/login")

    destination = request.form.get("destination")

    source_path = get_file_path(filename)

    if destination == "":
        destination_path = get_file_path(os.path.basename(filename))
        new_location = "/"
    else:
        destination_path = get_file_path(os.path.join(destination, os.path.basename(filename)))
        new_location = destination

    if not os.path.exists(source_path):
        flash("File not found", "error")
        return redirect("/")

    shutil.move(source_path, destination_path)

    metadata = load_metadata()

    if filename in metadata:
        metadata[os.path.join(destination, os.path.basename(filename)) if destination else os.path.basename(filename)] = metadata.pop(filename)
        metadata[os.path.join(destination, os.path.basename(filename)) if destination else os.path.basename(filename)]["location"] = new_location

    save_metadata(metadata)

    flash(f"Moved '{os.path.basename(filename)}' successfully", "success")
    return redirect("/")


@app.route("/bulk-bin", methods=["POST"])
def bulk_move_to_bin():
    if not has_access():
        return redirect("/login")

    selected_files = request.form.getlist("selected_files")

    if not selected_files:
        flash("No files selected", "error")
        return redirect("/")

    moved_count = 0

    for filename in selected_files:
        if is_protected_file(filename):
            continue

        file_path = get_file_path(filename)

        if os.path.exists(file_path):
            bin_path = os.path.join(BIN_FOLDER, os.path.basename(filename))

            counter = 1
            name, extension = os.path.splitext(os.path.basename(filename))

            while os.path.exists(bin_path):
                new_filename = f"{name}_deleted_{counter}{extension}"
                bin_path = os.path.join(BIN_FOLDER, new_filename)
                counter += 1

            shutil.move(file_path, bin_path)
            moved_count += 1

    flash(f"{moved_count} item(s) moved to Bin", "success")
    return redirect("/")


@app.route("/bulk-copy", methods=["POST"])
def bulk_copy_files():
    if not has_access():
        return redirect("/login")

    selected_files = request.form.getlist("selected_files")

    if not selected_files:
        flash("No files selected", "error")
        return redirect("/")

    copied_count = 0

    for filename in selected_files:
        original_path = get_file_path(filename)

        if not os.path.exists(original_path) or os.path.isdir(original_path):
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

        shutil.copy2(original_path, copied_path)

        metadata = get_file_metadata(filename)
        add_file_metadata(
            copied_relative_path,
            metadata["owner"],
            metadata["visibility"]
        )

        copied_count += 1

    flash(f"{copied_count} file(s) copied successfully", "success")
    return redirect("/")


@app.route("/bulk-toggle-visibility", methods=["POST"])
def bulk_toggle_visibility():
    if not has_access():
        return redirect("/login")

    selected_files = request.form.getlist("selected_files")

    if not selected_files:
        flash("No files selected", "error")
        return redirect("/")

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
    return redirect("/")


@app.route("/rename-page/<path:filename>")
def rename_page(filename):
    if not has_access():
        return redirect("/login")

    return render_template("rename_file.html", filename=filename)


@app.route("/rename/<path:filename>", methods=["POST"])
def rename_file(filename):
    if not has_access():
        return redirect("/login")

    new_name = request.form.get("new_name")

    if not new_name:
        flash("New name is required", "error")
        return redirect("/")

    old_path = get_file_path(filename)

    folder = os.path.dirname(filename)
    new_relative_path = os.path.join(folder, new_name) if folder else new_name
    new_path = get_file_path(new_relative_path)

    if not os.path.exists(old_path):
        flash("File not found", "error")
        return redirect("/")

    if os.path.exists(new_path):
        flash("A file with this name already exists", "error")
        return redirect("/")

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


@app.route("/bulk-move-page", methods=["POST"])
def bulk_move_page():
    if not has_access():
        return redirect("/login")

    selected_files = request.form.getlist("selected_files")

    if not selected_files:
        flash("No files selected", "error")
        return redirect("/")

    folders = get_folders()

    return render_template(
        "bulk_move.html",
        selected_files=selected_files,
        folders=folders
    )


@app.route("/bulk-move", methods=["POST"])
def bulk_move():
    if not has_access():
        return redirect("/login")

    selected_files = request.form.getlist("selected_files")
    destination = request.form.get("destination")

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
    return redirect("/")


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