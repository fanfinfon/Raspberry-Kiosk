import os
import requests
import redis
import json
from dotenv import load_dotenv
from datetime import datetime

# Load Redis URL
load_dotenv()
REDIS_URL = os.getenv("REDIS_URL")
r = redis.from_url(REDIS_URL)

# Local folder for images
IMAGE_FOLDER = "/home/caglar/Desktop/Kiosk/images"
os.makedirs(IMAGE_FOLDER, exist_ok=True)

def build_drive_download_url(photo_id: str) -> str:
    """
    Converts a Google Drive file ID into a direct download URL.
    """
    return f"https://drive.google.com/uc?export=download&id={photo_id}"

def download_from_drive(photo_id, photo_name):
    """
    Downloads a file from Google Drive using its file ID.
    """
    try:
        download_url = build_drive_download_url(photo_id)
        save_path = os.path.join(IMAGE_FOLDER, f"{photo_name}.jpg")

        if os.path.exists(save_path):
            print(f"✅ File already exists: {photo_name}.jpg")
            return True

        print(f"⬇️ Downloading {photo_name} from Google Drive...")
        resp = requests.get(download_url, timeout=30)

        if resp.status_code == 200 and resp.content.startswith(b'\xff\xd8'):  # JPEG check
            with open(save_path, "wb") as f:
                f.write(resp.content)
            print(f"✅ Saved: {photo_name}.jpg")
            return True
        elif resp.status_code == 200:
            # Still save non-JPG formats if response looks valid
            with open(save_path, "wb") as f:
                f.write(resp.content)
            print(f"✅ Saved non-JPG: {photo_name}")
            return True
        else:
            print(f"❌ Failed to download {photo_name}, status {resp.status_code}")
            return False

    except Exception as e:
        print(f"❌ Error downloading {photo_name}: {e}")
        return False

def sync_images():
    """
    Sync images from Redis (Google Drive-based) to local folder.
    """
    images_data = r.lrange("images", 0, -1)
    active_files = []

    for item in images_data:
        try:
            data = json.loads(item.decode())
        except Exception as e:
            print("❌ Could not parse item:", e)
            print("Raw data was:\n", item.decode())
            continue

        photo_id = data.get("photo_id")
        photo_name = data.get("photo_name", photo_id)
        status = data.get("status", "inactive")
        start_date = data.get("start_date")
        end_date = data.get("end_date")

        # Skip if missing file ID
        if not photo_id:
            print("⚠️ Missing photo_id, skipping...")
            continue

        # Optional scheduling control
        today = datetime.now().date()
        if start_date and end_date:
            try:
                start = datetime.strptime(start_date, "%Y-%m-%d").date()
                end = datetime.strptime(end_date, "%Y-%m-%d").date()
                if not (start <= today <= end):
                    print(f"📅 Skipping {photo_name}: out of date range.")
                    continue
            except:
                pass

        if status == "active":
            success = download_from_drive(photo_id, photo_name)
            if success:
                active_files.append(f"{photo_name}.jpg")
        else:
            print(f"🗑️ Skipping inactive entry {photo_name}")

    # Cleanup: remove local files not in active list
    for f in os.listdir(IMAGE_FOLDER):
        if f not in active_files:
            print(f"🗑️ Cleaning up old file {f}")
            os.remove(os.path.join(IMAGE_FOLDER, f))

if __name__ == "__main__":
    sync_images()
