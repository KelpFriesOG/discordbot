import os
import json

# Always resolve path relative to *this file*'s location
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.abspath(os.path.join(CURRENT_DIR, "..", "data", "profiles_data.json"))

print("💾 DATA_PATH resolved to:", DATA_PATH)

def load_profiles():
    if os.path.exists(DATA_PATH):
        with open(DATA_PATH, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if content:
                return json.loads(content)
    return {}

def save_profiles(data):
    print(f"Saving to {DATA_PATH}")
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)