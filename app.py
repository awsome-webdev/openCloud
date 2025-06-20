from flask import Flask, render_template, jsonify, request, send_from_directory, redirect, url_for, send_file, session
import os
from werkzeug.utils import secure_filename
import io
import zipfile
from functools import wraps
import logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
    filename='app.log',  # Log to a file
)
with open(f'{os.getcwd()}/users.txt', 'r') as f:
    file = f.read()
    print(file)

USERS = {}
for line in file.splitlines():
    username, password = line.split(':')
    USERS[username] = password

app = Flask(__name__)
with open('secret_key.txt', 'r') as key_file:
    secret_key = key_file.read().splitlines()[0]
    print(secret_key)
app.secret_key = secret_key  # Set a strong secret key!
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'root')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Helper to scan a directory and return its immediate contents
def scan_dir(path):
    tree = {}
    try:
        for entry in os.listdir(path):
            full_path = os.path.join(path, entry)
            if os.path.isdir(full_path):
                tree[entry] = {}
            else:
                tree[entry] = None
    except Exception as e:
        pass  # Optionally log error
    return tree

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def home():
    return render_template('login.html')
@app.route('/app')
@login_required
def app_home():
    return render_template('index.html')
@app.route('/tree')
@login_required
def tree():
    rel_path = request.args.get('path', '').strip('/')
    abs_path = os.path.join(app.config['UPLOAD_FOLDER'], rel_path) if rel_path else app.config['UPLOAD_FOLDER']
    if not os.path.commonpath([os.path.abspath(abs_path), app.config['UPLOAD_FOLDER']]) == app.config['UPLOAD_FOLDER']:
        return jsonify({})  # Prevent directory traversal
    return jsonify(scan_dir(abs_path))

@app.route('/upload', methods=['POST'])
@login_required
def upload():
    client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    logging.info(f"File upload attempt from IP: {client_ip} as {session['user']}")
    rel_path = request.args.get('path', '').strip('/')
    upload_dir = os.path.join(app.config['UPLOAD_FOLDER'], rel_path) if rel_path else app.config['UPLOAD_FOLDER']
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir)
    if 'file' not in request.files:
        return 'No file part', 400
    file = request.files['file']
    if file.filename == '':
        return 'No selected file', 400
    filename = secure_filename(file.filename)
    file.save(os.path.join(upload_dir, filename))
    return 'File uploaded', 200

@app.route('/download')
@login_required
def download():
    client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    logging.info(f"File download attempt from IP: {client_ip} as {session['user']}")
    rel_path = request.args.get('path', '').strip('/')
    if not rel_path:
        return 'No file specified', 400
    abs_path = os.path.join(app.config['UPLOAD_FOLDER'], rel_path)
    if not os.path.commonpath([os.path.abspath(abs_path), app.config['UPLOAD_FOLDER']]) == app.config['UPLOAD_FOLDER']:
        return 'Invalid path', 400
    if os.path.isfile(abs_path):
        dir_name = os.path.dirname(abs_path)
        file_name = os.path.basename(abs_path)
        return send_from_directory(directory=dir_name, path=file_name, as_attachment=True)
    elif os.path.isdir(abs_path):
        # Zip the folder in memory
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(abs_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, os.path.dirname(abs_path))
                    zipf.write(file_path, arcname)
        zip_buffer.seek(0)
        zip_filename = os.path.basename(abs_path.rstrip('/\\')) + '.zip'
        return send_file(zip_buffer, mimetype='application/zip', as_attachment=True, download_name=zip_filename)
    else:
        return 'File or folder not found', 404

@app.route('/login', methods=['GET', 'POST'])
def login():
    user_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    logging.info(f"Login attempt from IP: {user_ip} as {request.form.get('username')}")
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username in USERS and USERS[username] == password:
            session['user'] = username
            logging.info(f"User logged in: {username} from IP: {user_ip}")
            return redirect(url_for('app_home'))
        else:
            logging.warning(f"Failed login attempt for user: {username} from IP: {user_ip}")
            return render_template('login.html', error='Invalid credentials')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True, port=8080)