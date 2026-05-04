# This creates a basic flask web server for the smart home pi, the server allows users to upload files and stores them in the project storage folder.
# Features:
# - upload files
# - list stored files
# - download files

import os
from datetime import timedelta
from flask import Flask, request, send_from_directory, redirect, session

# Create flask application instance
app = Flask(__name__)

# Secret key used by Flask to protect login sessions
app.secret_key = "12345"

# Login session will stay active for 30 minutes
app.permanent_session_lifetime = timedelta(minutes=30)

# Define where uploaded files will be saved
UPLOAD_FOLDER = "/mnt/hdd"

# Admin devices with reserved/static IP addresses
ADMIN_IPS = [
    "192.168.1.99", # pc
    "192.168.1.108", # laptop
    "192.168.1.146" # tiago phone
]

# Password required for non-admin devices
ACCESS_PASSWORD = "123"

# Files/folders that should not appear or be modified
PROTECTED_ITEMS = ["System Volume Information"]

# Create the storage fodler if it does not already exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# this function will check out if user is admin and from there decide which home page user gets
def has_access():
    # Get the IP address of the device accessing the server
    user_ip = request.remote_addr

    # Admin devices can access without login page
    if user_ip in ADMIN_IPS:
        return True

    # Other devices need an active login session
    return session.get("logged_in") == True


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
    files = [
        f for f in os.listdir(UPLOAD_FOLDER)
        if f not in PROTECTED_ITEMS and not f.startswith(".")
    ]

    # Build HTML page with a list of files
    file_list_html = ""
    for file in files:
        file_list_html += f'''
        <li>
            <a href="/download/{file}">{file}</a>
            <form action="/delete/{file}" method="post" style="display:inline;">
                <button type="submit">Delete</button>
            </form>
        </li>
        '''

    return f"""
    <h1>Smart Home Cloud Pi</h1>
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
    # Check if the request contains a file
    if "file" not in request.files:
        return "No file selected"

    file = request.files["file"]

    # Check if the file has a name
    if file.filename == "":
        return "No file selected"

    # Create the full save path inside the storage folder
    save_path = os.path.join(UPLOAD_FOLDER, file.filename)
    # Save the uploaded file to the Raspberry Pi
    file.save(save_path)

    return f"File '{file.filename}' uploaded successfully <br><a href='/'>Back</a>"


# download route
@app.route("/download/<filename>")
def download_file(filename):
    if not has_access():
        return redirect("/login")
    
    if filename in PROTECTED_ITEMS or filename.startswith("."):
        return "Action not allowed"
            
    return send_from_directory(UPLOAD_FOLDER, filename, as_attachment=True)


# delete route
@app.route("/delete/<filename>", methods=["POST"])
def delete_file(filename):
    if not has_access():
        return redirect("/login")
    
    # Prevent deleting protected or hidden files
    if filename in PROTECTED_ITEMS or filename.startswith("."):
        return "Action not allowed"

    # Create the full path to the selected file
    file_path = os.path.join(UPLOAD_FOLDER, filename)

    # Check if the file exists before trying to delete it
    if os.path.exists(file_path):
        os.remove(file_path)

    # Send the user back to the home page after deleting
    return redirect("/")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


# Run the Flask app
if __name__ == "__main__":
    # host="0.0.0.0" allows other devices on the WiFi network to access the app
    app.run(host="0.0.0.0", port=5000)