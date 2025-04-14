
import os
import json

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.abspath(os.path.join(CURRENT_DIR, "..", "data", "playlists_data.json"))

print("🎵 Playlist DATA_PATH:", DATA_PATH)

def load_playlists():
    if os.path.exists(DATA_PATH):
        with open(DATA_PATH, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if content:
                return json.loads(content)
    return {}

def save_playlists(data):
    print(f"Saving playlist data to {DATA_PATH}")
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)