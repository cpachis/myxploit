import os
import json
from flask import current_app
from flask_login import UserMixin

class User(UserMixin):
    def __init__(self, username):
        self.id = username
    @property
    def is_active(self):
        return True

def load_json(fname):
    path = os.path.join(current_app.root_path, 'data', fname)
    if os.path.exists(path):
        with open(path, encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_json(fname, data):
    with open(os.path.join(current_app.root_path, 'data', fname), 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4) 