import os
import requests
import redis
import json
from dotenv import load_dotenv

# Load Redis URL
load_dotenv()
REDIS_URL = os.getenv("REDIS_URL")
r = redis.from_url(REDIS_URL)

# Local folder for images
IMAGE_FOLDER = "/home/caglar/Desktop/Kiosk/images"
os.makedirs(IMAGE_FOLDER, exist_ok=True)

def download_from_gofile(photo_id, bearer, filename, filepath):
    """
    Get the real file link from GoFile API and download it.
    """
    try:
        api_url = f"https://api.gofile.io/getContent?contentId={photo_id}&token={bearer}"
        resp = requests.get(api_url, timeout=30)
        data = resp.json()

        if data.get("status") == "ok":
            files = data["data"]["contents"]
            if not files:
                print(f"⚠️ No files found for {photo_id}")
                return False

            first_file = next(iter(files.values()))
            direct_url = first_file["link"]

            print(f"⬇️ Downloading {filename} from {direct_url}...")
            img_resp = requests.get(direct_url, timeout=30)
            if img_resp.status_code == 200:
                with open(filepath, "wb") as f:
                    f.write(img_resp.content)
                return True
            else:
                print(f"❌ Failed to download {filename}, status {img_resp.status_code}")
        else:
            print(f"❌ GoFile API error for {photo_id}: {data}")
    except Exception as e:
        print("❌ Error in GoFile download:", e)
    return False

def sync_images():
    # Fetch all items from Redis list "images"
    images_data = r.lrange("images", 0, -1)
    active_files = []

    for item in images_data:
        try:
            data = json.loads(item.decode())
        except Exception as e:
            print("❌ Could not parse item:", e)
            print("Raw data was:\n", item.decode())
            continue

        url = data.get("photo_url")
        photo_id = data.get("photo_id")
        bearer = data.get("photo_bearer")
        status = data.get("status")

        if not url or not photo_id or not bearer:
            print("⚠️ Missing fields in entry, skipping...")
            continue

        filename = os.path.basename(url)
        filepath = os.path.join(IMAGE_FOLDER, filename)

        if status == "active":
            active_files.append(filename)
            if not os.path.exists(filepath):
                success = download_from_gofile(photo_id, bearer, filename, filepath)
                if not success:
                    print(f"⚠️ Could not download {filename}")
        else:
            if os.path.exists(filepath):
                print(f"🗑️ Deleting {filename} (inactive)...")
                os.remove(filepath)

    # Cleanup: remove local files not active anymore
    for f in os.listdir(IMAGE_FOLDER):
        if f not in active_files:
            print(f"🗑️ Cleaning up old file {f}")
            os.remove(os.path.join(IMAGE_FOLDER, f))

if __name__ == "__main__":
    sync_images()
