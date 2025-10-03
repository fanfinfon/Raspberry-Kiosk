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
    Get the real file link from GoFile API (anonymous uploads with guest token) and download it.
    """
    try:
        api_url = f"https://api.gofile.io/contents/{photo_id}"
        headers = {"Authorization": f"Bearer {bearer}"}
        resp = requests.get(api_url, headers=headers, timeout=30)

        try:
            data = resp.json()
        except Exception:
            print(f"⚠️ GoFile API returned non-JSON for {photo_id}")
            print("Response text was:\n", resp.text[:300])
            return False

        if data.get("status") == "ok":
            contents = data["data"]["contents"]
            if not contents:
                print(f"⚠️ No files found in folder {photo_id}")
                return False

            # Download ALL files in this folder
            for file_id, file_info in contents.items():
                direct_url = file_info["link"]
                real_name = file_info["name"]

                save_path = os.path.join(IMAGE_FOLDER, real_name)
                if not os.path.exists(save_path):
                    print(f"⬇️ Downloading {real_name} from {direct_url}...")
                    img_resp = requests.get(direct_url, timeout=30)
                    if img_resp.status_code == 200:
                        with open(save_path, "wb") as f:
                            f.write(img_resp.content)
                    else:
                        print(f"❌ Failed to download {real_name}, status {img_resp.status_code}")
            return True
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

        photo_id = data.get("photo_id")
        bearer = data.get("photo_bearer")
        status = data.get("status")

        if not photo_id or not bearer:
            print("⚠️ Missing photo_id or bearer, skipping...")
            continue

        if status == "active":
            # Track active files by asking GoFile what’s inside the folder
            api_url = f"https://api.gofile.io/contents/{photo_id}"
            resp = requests.get(api_url, headers={"Authorization": f"Bearer {bearer}"}, timeout=30)
            try:
                data_info = resp.json()
                if data_info.get("status") == "ok":
                    for file_id, file_info in data_info["data"]["contents"].items():
                        active_files.append(file_info["name"])
                else:
                    print(f"⚠️ API error when checking active files for {photo_id}: {data_info}")
            except:
                print("⚠️ Could not parse GoFile folder info.")
            
            # Download files
            download_from_gofile(photo_id, bearer, photo_id, IMAGE_FOLDER)
        else:
            print(f"🗑️ Skipping inactive entry {photo_id}")

    # Cleanup: remove local files not in active list
    for f in os.listdir(IMAGE_FOLDER):
        if f not in active_files:
            print(f"🗑️ Cleaning up old file {f}")
            os.remove(os.path.join(IMAGE_FOLDER, f))

if __name__ == "__main__":
    sync_images()
