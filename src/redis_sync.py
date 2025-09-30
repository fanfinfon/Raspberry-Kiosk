# redis_sync.py
import os
import redis
import requests
from dotenv import load_dotenv

# Load env variables
load_dotenv()

redis_url = os.getenv("REDIS_URL")
r = redis.Redis.from_url(redis_url, decode_responses=True)

active_urls = set()

def sync_images(image_folder):
    global active_urls

    if not os.path.exists(image_folder):
        os.makedirs(image_folder)

    keys = r.keys("*")
    new_active = set()

    for key in keys:
        data = r.hgetall(key)
        if data.get("status") == "active":
            url = data.get("url")
            if url:
                new_active.add(url)
                filename = os.path.join(image_folder, os.path.basename(url))
                if not os.path.exists(filename):
                    try:
                        resp = requests.get(url, timeout=10)
                        with open(filename, "wb") as f:
                            f.write(resp.content)
                        print(f"Downloaded new: {filename}")
                    except Exception as e:
                        print(f"Failed to download {url}: {e}")

    to_remove = active_urls - new_active
    for url in to_remove:
        filename = os.path.join(image_folder, os.path.basename(url))
        if os.path.exists(filename):
            os.remove(filename)
            print(f"Deleted deactivated: {filename}")

    active_urls = new_active

    return [
        os.path.join(image_folder, f)
        for f in os.listdir(image_folder)
        if f.endswith((".png", ".jpg", ".jpeg", ".webp"))
    ]
