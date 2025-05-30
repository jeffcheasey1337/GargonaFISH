import json
import os

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KEYBINDS_PATH = os.path.join(ROOT_DIR, 'config', 'keybinds.json')

def read_binded_key():
    if not os.path.exists(KEYBINDS_PATH):
        return None
    try:
        with open(KEYBINDS_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('fishing_key')
    except Exception:
        return None

def save_binded_key(key):
    data = {}
    if os.path.exists(KEYBINDS_PATH):
        try:
            with open(KEYBINDS_PATH, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception:
            data = {}

    data['fishing_key'] = key

    with open(KEYBINDS_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
