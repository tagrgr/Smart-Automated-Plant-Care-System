# This creates a basic flask web server for the smart home pi, the server allows users to upload files and stores them in the project storage folder.
# Main app for our Home Server

import os
from flask import Flask, request, send_from_directory, redirect, session

from config import (
    UPLOAD_FOLDER,
    ACCESS_PASSWORD,
    SECRET_KEY,
    SESSION_LIFETIME
)

from auth import has_access
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

    return """
    <h1>Smart Home Cloud Pi Login</h1>

    <form method="post">
        <input type="password" name="password" placeholder="Enter password">
        <button type="submit">Login</button>
    </form>
    """


# Define route for homepage
@app.route("/")
def home():
    if not has_access():
        return redirect("/login")

    # Get list of files from storage and hide System Volume Information directory  and hidden system files as they're useless for our project 
    files = get_visible_files()

    # Build HTML page with a list of files
    file_list_html = ""
    for file in files:
        file_list_html += f'''
        <li>
            <a href="/download/{file}">{file}</a>

            <form action="/info/{file}" method="get" style="display:inline;">
                <button type="submit">Info</button>
            </form>

            <form action="/confirm-delete/{file}" method="get" style="display:inline;">
                <button type="submit">Delete</button>
            </form>

        </li>
        '''

    return f"""
    <h1>Smart Home Cloud Pi</h1>

    <a href="/logout">Logout</a>

    <h2>Upload File</h2>

    <form action="/upload" method="post" enctype="multipart/form-data">
        <input type="file" name="file">
        <button type="submit">Upload</button>
    </form>

    <h2>Stored Files</h2>
    <ul>
        {file_list_html}
    </ul>
    """


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

    # # Get file size in bytes
    # file_size = os.path.getsize(file_path)

    # # Convert file size to MB for easier reading
    # file_size_mb = round(file_size / (1024 * 1024), 2)

    # # Get the last modified time and convert it to readable format
    # modified_time = os.path.getmtime(file_path)
    # modified_date = datetime.fromtimestamp(modified_time).strftime("%d/%m/%Y %H:%M")

    return f'''
    <h1>File Information</h1>

    <p><strong>File name:</strong> {info["filename"]}</p>
    <p><strong>File size:</strong> {info["size_mb"]} MB</p>
    <p><strong>Last modified:</strong> {info["modified_date"]}</p>
    <p><strong>Storage location:</strong> {info["location"]}</p>

    <br>
    <a href="/">Back</a>
    '''


@app.route("/confirm-delete/<filename>")
def confirm_delete(filename):
    if not has_access():
        return redirect("/login")

    # Prevent system/hidden files
    if is_protected_file(filename):
        return "Action not allowed"

    return f'''
    <h2>Are you sure you want to delete '{filename}'?</h2>

    <form action="/delete/{filename}" method="post">
        <button type="submit">Yes, delete</button>
    </form>

    <br>

    <a href="/">Cancel</a>
    '''


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


# @app.route("/my-ip")
# def my_ip():
#     return f"Your IP is: {request.remote_addr}"


# Run the Flask app
if __name__ == "__main__":
    # host="0.0.0.0" allows other devices on the WiFi network to access the app
    app.run(host="0.0.0.0", port=5000)