import os
import requests
import redis
import json
import ast
from dotenv import load_dotenv

# Load Redis URL
load_dotenv()
REDIS_URL = os.getenv("REDIS_URL")
r = redis.from_url(REDIS_URL)

IMAGE_FOLDER = "/home/caglar/Desktop/Kiosk/images"
os.makedirs(IMAGE_FOLDER, exist_ok=True)

def parse_redis_item(raw_bytes):
    text = raw_bytes.decode().strip()
    try:
        # Try JSON parse
        return json.loads(text)
    except json.JSONDecodeError:
        try:
            # Fallback: try Python dict format
            return ast.literal_eval(text)
        except Exception as e:
            print("❌ Could not parse item:", e)
            print("Raw data was:\n", text)
            return None

def sync_images():
    images_data = r.lrange("images", 0, -1)  # list of bytes
    active_files = []

    for item in images_data:
        data = parse_redis_item(item)
        if not data:
            continue  # skip bad items

        url = data.get("photo_url")
        status = data.get("status")
        filename = os.path.basename(url)
        filepath = os.path.join(IMAGE_FOLDER, filename)

        if status == "active":
            active_files.append(filename)
            if not os.path.exists(filepath):
                print(f"⬇️ Downloading {filename}...")
                resp = requests.get(url, timeout=30)
                if resp.status_code == 200:
                    with open(filepath, "wb") as f:
                        f.write(resp.content)
        else:
            if os.path.exists(filepath):
                print(f"🗑️ Deleting {filename} (inactive)...")
                os.remove(filepath)

    # Cleanup files not in active list
    for f in os.listdir(IMAGE_FOLDER):
        if f not in active_files:
            os.remove(os.path.join(IMAGE_FOLDER, f))

if __name__ == "__main__":
    sync_images()

