import os
import requests
import redis
from dotenv import load_dotenv

# Load Redis URL
load_dotenv()
REDIS_URL = os.getenv("REDIS_URL")
r = redis.from_url(REDIS_URL)

IMAGE_FOLDER = "/home/caglar/Desktop/Kiosk/images"
os.makedirs(IMAGE_FOLDER, exist_ok=True)

def sync_images():
    images_data = r.hgetall("image")  # Assuming Redis hash key = "image"
    active_files = []

    for key, value in images_data.items():
        try:
            # Assuming Redis stores like: {"url":"http://...","status":"active"}
            data = eval(value.decode())  
            url = data.get("url")
            status = data.get("status")
            filename = os.path.basename(url)
            filepath = os.path.join(IMAGE_FOLDER, filename)

            if status == "active":
                active_files.append(filename)
                if not os.path.exists(filepath):
                    print(f"Downloading {filename}...")
                    resp = requests.get(url, timeout=30)
                    if resp.status_code == 200:
                        with open(filepath, "wb") as f:
                            f.write(resp.content)
            else:
                if os.path.exists(filepath):
                    print(f"Deleting {filename} (inactive)...")
                    os.remove(filepath)

        except Exception as e:
            print(f"Error processing {key}: {e}")

    # Remove files not in active list
    for f in os.listdir(IMAGE_FOLDER):
        if f not in active_files:
            os.remove(os.path.join(IMAGE_FOLDER, f))

if __name__ == "__main__":
    sync_images()
