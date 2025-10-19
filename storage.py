import json
import os
import threading
from typing import Any, Dict

_lock = threading.Lock()

def ensure_file(path: str, default: Any):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if not os.path.exists(path):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(default, f, ensure_ascii=False, indent=2)

def read_json(path: str) -> Any:
    ensure_file(path, default={})
    with _lock:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

def write_json(path: str, data: Any):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with _lock:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

def get_user(users_path: str, user_id: int) -> Dict:
    users = read_json(users_path)
    u = users.get(str(user_id), {})
    if not u:
        u = {
            "font": "normal",          # small | normal | big | code
            "feedback_popup": True,    # show post-deepseek popup
            "deepseek_mode": "normal"  # normal | coder
        }
        users[str(user_id)] = u
        write_json(users_path, users)
    return u

def set_user(users_path: str, user_id: int, key: str, value):
    users = read_json(users_path)
    u = users.get(str(user_id), {})
    u[key] = value
    users[str(user_id)] = u
    write_json(users_path, users)

def add_file(files_path: str, file_entry: Dict):
    files = read_json(files_path)
    files.setdefault("items", [])
    files["items"].append(file_entry)
    write_json(files_path, files)

def list_files(files_path: str):
    files = read_json(files_path)
    return files.get("items", [])