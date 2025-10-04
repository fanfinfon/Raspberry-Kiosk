import os
import subprocess

# Paths
PROJECT_DIR = "/home/caglar/Desktop/Kiosk"
IMAGE_DIR = os.path.join(PROJECT_DIR, "images")
SYNC_SCRIPT = os.path.join(PROJECT_DIR, "sync_images.py")
PYTHON = "/usr/bin/python3"

def create_image_folder():
    if not os.path.exists(IMAGE_DIR):
        os.makedirs(IMAGE_DIR)
        print(f"Created folder: {IMAGE_DIR}")
    else:
        print(f"Folder already exists: {IMAGE_DIR}")

def install_cronjob():
    job = f"*/5 * * * * {PYTHON} {SYNC_SCRIPT}\n"

    # Get current crontab for this user
    result = subprocess.run(["crontab", "-l"], capture_output=True, text=True)
    current_cron = result.stdout if result.returncode == 0 else ""

    # Add job if not already installed
    if job not in current_cron:
        new_cron = current_cron + job
        process = subprocess.run(["crontab"], input=new_cron, text=True)
        if process.returncode == 0:
            print("✅ Cronjob installed (runs every 5 minutes).")
        else:
            print("❌ Failed to install cronjob.")
    else:
        print("ℹ️ Cronjob already exists.")

def run_first_sync():
    print("Running first sync...")
    subprocess.run([PYTHON, SYNC_SCRIPT])

if __name__ == "__main__":
    create_image_folder()
    install_cronjob()
    run_first_sync()
    print("🎉 Setup complete! Now run kiosk.py to start the slideshow.")
