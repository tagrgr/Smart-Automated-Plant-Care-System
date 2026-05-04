# This creates a basic flask web server for the smart home pi, the server allows users to upload files and stores them in the project storage folder.
# Main app for our Home Server

import os
from flask import Flask, render_template, request, send_from_directory, redirect, url_for, session

from config import (
    UPLOAD_FOLDER,
    ACCESS_PASSWORD,
    SECRET_KEY,
    SESSION_LIFETIME
)

from auth import has_access, get_current_user
from file_manager import (
    get_visible_files,
    is_protected_file,
    get_file_path,
    get_file_info
)

# Create flask application instance
app = Flask(__name__)

# Configure Flask session security and timeout
app.secret_key = SECRET_KEY
app.permanent_session_lifetime = SESSION_LIFETIME

# Make sure the upload fodler exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


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
    # Get list of files from storage and hide System Volume Information directory  and hidden system files as they're useless for our project 
    files = get_visible_files()

    return render_template(
        "home.html",
        current_user=current_user,
        files=files
    )


# Upload route
@app.route("/upload", methods=["POST"])
def upload_file():
    if not has_access():
        return redirect("/login")

    # Check if the request contains a file
    if "file" not in request.files:
        return "No file selected"

    file = request.files["file"]

    # Check if the file has a name
    if file.filename == "":
        return "No file selected"

    # Create the full save path inside the storage folder
    save_path = get_file_path(file.filename)
    # Save the uploaded file to the Raspberry Pi
    file.save(save_path)

    return f"File '{file.filename}' uploaded successfully <br><a href='/'>Back</a>"


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
        return "Action not allowed"

    # Create the full path to the selected file
    file_path = get_file_path(filename)

    # Check if the file exists before trying to delete it
    if os.path.exists(file_path):
        os.remove(file_path)

    # Send the user back to the home page after deleting
    return redirect("/")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


@app.route("/my-ip")
def my_ip():
    return f"Your IP is: {request.remote_addr}"


# Run the Flask app
if __name__ == "__main__":
    # host="0.0.0.0" allows other devices on the WiFi network to access the app
    app.run(host="0.0.0.0", port=5000)