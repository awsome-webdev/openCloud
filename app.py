from flask import Flask, render_template, jsonify
import os
import json

app = Flask(__name__)

def scan_dir(path):
    def build_tree(current_path):
        tree = {}
        for entry in os.listdir(current_path):
            full_path = os.path.join(current_path, entry)
            if os.path.isdir(full_path):
                tree[entry] = build_tree(full_path)
            else:
                tree[entry] = None
        return tree

    return build_tree(path)
@app.route('/')
def home():
    return render_template('index.html')
@app.route('/tree')
def tree():
    return jsonify(scan_dir(f"{os.getcwd()}/root/"))

if __name__ == '__main__':
    app.run(debug=True, port=8080)