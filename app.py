from flask import Flask, render_template, jsonify, request, send_from_directory, redirect, url_for, send_file, session
import os
from werkzeug.utils import secure_filename
import io
import zipfile
from functools import wraps
import logging
from werkzeug.middleware.proxy_fix import ProxyFix
import argparse
from flask_socketio import SocketIO
import os
import subprocess
import select
import struct
import shlex
import logging
import sys
import platform
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
socketio = SocketIO(app)

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
@app.route('/save', methods=['POST'])
@login_required
def save():
    client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    logging.info(f"Save attempt from IP: {client_ip} as {session.get('user', 'guest')}")
    rel_path = request.args.get('path', '').strip('/')
    content = request.form.get('content', '')
    abs_path = os.path.join(app.config['UPLOAD_FOLDER'], rel_path)
    if not os.path.commonpath([os.path.abspath(abs_path), app.config['UPLOAD_FOLDER']]) == app.config['UPLOAD_FOLDER']:
        return 'Invalid path', 400
    if not os.path.exists(os.path.dirname(abs_path)):
        os.makedirs(os.path.dirname(abs_path))
    with open(abs_path, 'w') as f:
        f.write(content)
    return 'File saved', 200
@app.route('/rename',)
@login_required
def rename():
    client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    logging.info(f"Rename attempt from IP: {client_ip} as {session['user']}")
    rel_path = request.args.get('path', '').strip('/')
    new_name = request.args.get('new_name', '').strip()
    abs_path = os.path.join(app.config['UPLOAD_FOLDER'], rel_path)
    if not os.path.commonpath([os.path.abspath(abs_path), app.config['UPLOAD_FOLDER']]) == app.config['UPLOAD_FOLDER']:
        return 'Invalid path', 400
    if not os.path.exists(abs_path):
        return 'File or directory not found', 404
    new_abs_path = os.path.join(os.path.dirname(abs_path), new_name)
    if os.path.exists(new_abs_path):
        return 'New name already exists', 400
    os.rename(abs_path, new_abs_path)
    return 'Renamed successfully', 200
@app.route('/app')
@login_required
def app_home():
    return render_template('index.html')
@app.route('/mobile')
@login_required
def mobile_home():
    return render_template('mobile-index.html')
@app.route('/makefolder')
@login_required
def makefolder():
    client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    logging.info(f"Folder creation attempt from IP: {client_ip} as {session['user']}")
    rel_path = request.args.get('path', '').strip('/')
    folder_name = request.args.get('name', '').strip()
    abs_path = os.path.join(app.config['UPLOAD_FOLDER'], rel_path, folder_name)
    if not os.path.commonpath([os.path.abspath(abs_path), app.config['UPLOAD_FOLDER']]) == app.config['UPLOAD_FOLDER']:
        return 'Invalid path', 400
    if not os.path.exists(abs_path):
        os.makedirs(abs_path)
        return 'Folder created', 200
    else:
        return 'Folder already exists', 400
@app.route('/tree')
@login_required
def tree():
    rel_path = request.args.get('path', '').strip('/')
    abs_path = os.path.join(app.config['UPLOAD_FOLDER'], rel_path) if rel_path else app.config['UPLOAD_FOLDER']
    if not os.path.commonpath([os.path.abspath(abs_path), app.config['UPLOAD_FOLDER']]) == app.config['UPLOAD_FOLDER']:
        return jsonify({})  # Prevent directory traversal
    return jsonify(scan_dir(abs_path))
@app.route('/delete', methods=['GET'])
@login_required
def delete():
    client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    logging.info(f"File delete attempt from IP: {client_ip} as {session['user']}")
    rel_path = request.args.get('path', '').strip('/')
    abs_path = os.path.join(app.config['UPLOAD_FOLDER'], rel_path)
    if not os.path.commonpath([os.path.abspath(abs_path), app.config['UPLOAD_FOLDER']]) == app.config['UPLOAD_FOLDER']:
        return 'Invalid path', 400
    if os.path.isfile(abs_path):
        os.remove(abs_path)
        return 'File deleted', 200
    elif os.path.isdir(abs_path):
        os.rmdir(abs_path)
        return 'Directory deleted', 200
    else:
        return 'File or directory not found', 404
@app.route('/file')
@login_required
def file():
    rel_path = request.args.get('path', '').strip('/')
    abs_path = os.path.join(app.config['UPLOAD_FOLDER'], rel_path)
    # Directory traversal protection
    if not os.path.commonpath([os.path.abspath(abs_path), app.config['UPLOAD_FOLDER']]) == app.config['UPLOAD_FOLDER']:
        return 'Invalid path', 400
    if not os.path.isfile(abs_path):
        return 'File not found', 404
    return send_file(abs_path)
@app.route('/upload', methods=['POST'])
@login_required
def upload():
    client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    logging.info(f"File upload attempt from IP: {client_ip} as {session['user']}")
    rel_path = request.args.get('path', '').strip('/')
    upload_dir = os.path.join(app.config['UPLOAD_FOLDER'], rel_path) if rel_path else app.config['UPLOAD_FOLDER']
    if not os.path.commonpath([os.path.abspath(upload_dir), app.config['UPLOAD_FOLDER']]) == app.config['UPLOAD_FOLDER']:
        return 'Invalid path', 400
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir)
    if 'file' not in request.files and 'files[]' not in request.files:
        return 'No file part', 400
    files = request.files.getlist('file')
    if not files or files == [None]:
        files = request.files.getlist('files[]')
    if not files or files == [None]:
        return 'No selected file', 400
    for file in files:
        if file.filename == '':
            continue
        filename = secure_filename(file.filename)
        file.save(os.path.join(upload_dir, filename))
    return 'File(s) uploaded', 200
@app.route('/move')
@login_required
def move():
    #client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    #logging.info(f"File move attempt from IP: {client_ip} as {session['user']}")
    rel_path = request.args.get('path', '').strip('/')
    new_path = request.args.get('new_path', '').strip('/')
    abs_path = os.path.join(app.config['UPLOAD_FOLDER'], rel_path)
    new_abs_path = os.path.join(app.config['UPLOAD_FOLDER'], new_path)
    if not os.path.commonpath([os.path.abspath(abs_path), app.config['UPLOAD_FOLDER']]) == app.config['UPLOAD_FOLDER']:
        return 'Invalid path', 400
    if not os.path.commonpath([os.path.abspath(new_abs_path), app.config['UPLOAD_FOLDER']]) == app.config['UPLOAD_FOLDER']:
        return 'Invalid new path', 400
    if not os.path.exists(abs_path):
        return 'File or directory not found', 404
    if os.path.exists(new_abs_path):
        return 'New path already exists', 400
    os.rename(abs_path, new_abs_path)
    return 'Moved successfully', 200
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
if platform.system() == "Windows":
    @app.route('/terminal')
    def unsup():
        return "<h1>Shell is not suppported for windows</h1>"
else:
    import pty
    import termios
    import fcntl
    app.config["child_pid"] = None
    app.config["fd"] = None
    app.config["cmd"] = ["/bin/bash"]
    def set_winsize(fd, row, col, xpix=0, ypix=0):
        logging.debug("setting window size with termios")
        winsize = struct.pack("HHHH", row, col, xpix, ypix)
        fcntl.ioctl(fd, termios.TIOCSWINSZ, winsize)


    def read_and_forward_pty_output():
        max_read_bytes = 1024 * 20
        while True:
            socketio.sleep(0.01)
            if app.config["fd"]:
                timeout_sec = 0
                (data_ready, _, _) = select.select([app.config["fd"]], [], [], timeout_sec)
                if data_ready:
                    output = os.read(app.config["fd"], max_read_bytes).decode(
                        errors="ignore"
                    )
                    socketio.emit("pty-output", {"output": output}, namespace="/pty")


    @app.route("/terminal")
    @login_required
    def index():
        return render_template("terminal.html")


    @socketio.on("pty-input", namespace="/pty")
    @login_required
    def pty_input(data):
        """write to the child pty. The pty sees this as if you are typing in a real
        terminal.
        """
        if app.config["fd"]:
            logging.debug("received input from browser: %s" % data["input"])
            os.write(app.config["fd"], data["input"].encode())


    @socketio.on("resize", namespace="/pty")
    def resize(data):
        if app.config["fd"]:
            logging.debug(f"Resizing window to {data['rows']}x{data['cols']}")
            set_winsize(app.config["fd"], data["rows"], data["cols"])


    @socketio.on("connect", namespace="/pty")
    @login_required
    def connect():
        """new client connected"""
        logging.info("new client connected")
        if app.config["child_pid"]:
            # already started child process, don't start another
            return

        # create child process attached to a pty we can read from and write to
        (child_pid, fd) = pty.fork()
        if child_pid == 0:
            # this is the child process fork.
            # anything printed here will show up in the pty, including the output
            # of this subprocess
            subprocess.run(app.config["cmd"])
        else:
            # this is the parent process fork.
            # store child fd and pid
            app.config["fd"] = fd
            app.config["child_pid"] = child_pid
            set_winsize(fd, 50, 50)
            cmd = " ".join(shlex.quote(c) for c in app.config["cmd"])
            # logging/print statements must go after this because... I have no idea why
            # but if they come before the background task never starts
            socketio.start_background_task(target=read_and_forward_pty_output)

            logging.info("child pid is " + child_pid)
            logging.info(
                f"starting background task with command `{cmd}` to continously read "
                "and forward pty output to client"
            )
            logging.info("task started")
def main():
    green = "\033[92m"
    end = "\033[0m"
    log_format = (
        green
        + "pyxtermjs > "
        + end
        + "%(levelname)s (%(funcName)s:%(lineno)s) %(message)s"
    )
    logging.basicConfig(
        format=log_format,
        stream=sys.stdout,
        level=logging.INFO,
    )
    logging.info(f"serving on http://127.0.0.1:8080")
    socketio.run(app, debug=True, port='8080', host="0.0.0.0")

if __name__ == '__main__':
    main()