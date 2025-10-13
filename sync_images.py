import os
import json
import time
import redis
from PIL import Image
import requests
from dotenv import load_dotenv


# -------------------------
# Load Redis URL
# -------------------------
load_dotenv()
REDIS_URL = os.getenv("REDIS_URL")

# Try to connect to Redis safely
try:
    r = redis.from_url(REDIS_URL)
    r.ping()  # test connection
except Exception as e:
    print(f"Could not connect to Redis: {e}")
    r = None

# Local folder for saving images
IMAGE_FOLDER = "/home/caglar/Desktop/Kiosk/images"
os.makedirs(IMAGE_FOLDER, exist_ok=True)


def build_drive_download_url(file_id):
    """Convert Google Drive file ID to direct public download link."""
    return f"https://drive.google.com/uc?export=download&id={file_id}"


def is_valid_image(file_path):
    """Check if the downloaded file is a valid image using Pillow."""
    try:
        if not os.path.exists(file_path):
            return False
        if os.path.getsize(file_path) < 1024:
            return False
        with Image.open(file_path) as img:
            img.verify()  # checks header
        return True
    except Exception:
        return False


def download_from_drive(photo_id, photo_name):
    """
    Download a public Google Drive file using the provided photo_name.
    Includes retry logic, a 30-second timeout, and atomic (.tmp) saving.
    """
    download_url = build_drive_download_url(photo_id)
    save_path = os.path.join(IMAGE_FOLDER, photo_name)
    temp_path = save_path + ".tmp"

    # Skip if already exists
    if os.path.exists(save_path):
        return photo_name

    for attempt in range(3):
        try:
            resp = requests.get(download_url, stream=True, timeout=(10, 20))
            if resp.status_code != 200:
                print(f"Download failed for {photo_name}, status {resp.status_code}")
                continue

            print(f"Downloading {photo_name} (attempt {attempt+1})")
            with open(temp_path, "wb") as f:
                for chunk in resp.iter_content(8192):
                    if chunk:
                        f.write(chunk)

            os.replace(temp_path, save_path)  # atomic rename

            if not is_valid_image(save_path):
                print(f"Invalid file detected, removing {photo_name}")
                os.remove(save_path)
                return None

            print(f"Saved: {photo_name}")
            return photo_name

        except requests.exceptions.Timeout:
            print(f"Timeout while downloading {photo_name} (attempt {attempt+1})")
        except requests.exceptions.RequestException as e:
            print(f"Network error while downloading {photo_name} (attempt {attempt+1}): {e}")
        except Exception as e:
            print(f"Unexpected error downloading {photo_name} (attempt {attempt+1}): {e}")

        if attempt < 2:
            time.sleep(3)
        else:
            print(f"Failed to download {photo_name} after 3 attempts")
            return None


def sync_images():
    """
    Sync images from Redis to local folder.
    Expects a single JSON array stored under the 'images' key.
    """
    if not r:
        print("Redis connection not available. Aborting sync.")
        return

    # --- Cleanup leftover .tmp files from interrupted downloads ---
    for f in os.listdir(IMAGE_FOLDER):
        if f.endswith(".tmp"):
            tmp_path = os.path.join(IMAGE_FOLDER, f)
            try:
                os.remove(tmp_path)
                print(f"Removed leftover temporary file: {f}")
            except Exception as e:
                print(f"Failed to remove temporary file {f}: {e}")

    # --- Fetch and parse JSON data ---
    try:
        raw_data = r.execute_command("JSON.GET", "images")
        if not raw_data:
            print("No data found in Redis.")
            return
        images_data = json.loads(raw_data)
    except Exception as e:
        print(f"Failed to fetch or parse data from Redis: {e}")
        return


    active_files = []

    for data in images_data:
        photo_id = data.get("photo_id")
        photo_name = data.get("photo_name")
        status = data.get("status", "inactive")

        if not photo_id or not photo_name:
            continue

        if status == "active":
            file_name = download_from_drive(photo_id, photo_name)
            if file_name:
                active_files.append(file_name)

    # --- Cleanup old files ---
    for f in os.listdir(IMAGE_FOLDER):
        if f not in active_files and not f.endswith(".tmp"):
            print(f"Removing old file: {f}")
            os.remove(os.path.join(IMAGE_FOLDER, f))


if __name__ == "__main__":
    sync_images()
