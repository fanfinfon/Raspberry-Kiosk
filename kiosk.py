import pygame
import os

pygame.init()
screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
pygame.mouse.set_visible(False)

# Folder for synced images
image_folder = "/home/caglar/Desktop/Kiosk/images"

def load_images():
    """Get list of image file paths."""
    return [os.path.join(image_folder, f) for f in os.listdir(image_folder)
            if f.lower().endswith((".png", ".jpg", ".jpeg", ".webp", ".heic"))]

def preload_images():
    """Load, scale, and prepare all images before starting slideshow."""
    loaded = []
    screen_w, screen_h = screen.get_size()
    image_paths = load_images()

    for path in image_paths:
        try:
            img = pygame.image.load(path).convert()  # convert to display format
            img_w, img_h = img.get_size()

            # Scale proportionally
            scale = min(screen_w / img_w, screen_h / img_h)
            new_w, new_h = int(img_w * scale), int(img_h * scale)
            img = pygame.transform.smoothscale(img, (new_w, new_h))

            rect = img.get_rect(center=(screen_w // 2, screen_h // 2))
            loaded.append((img, rect))
        except Exception as e:
            print(f"Error preloading {path}: {e}")

    return loaded

images = preload_images()
running = True
index = 0
clock = pygame.time.Clock()
image_time = 0
delay = 5000  # 5 seconds per image

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_ESCAPE, pygame.K_q):
                running = False

    # Reload image list each full cycle
    if index == 0:
        images = preload_images()

    # Current time in ms
    current_time = pygame.time.get_ticks()

    if images and (current_time - image_time > delay):
        img, rect = images[index]
        screen.fill((0, 0, 0))
        screen.blit(img, rect)
        pygame.display.update()

        index = (index + 1) % len(images)
        image_time = current_time

        pygame.mouse.set_visible(False)  # ensure hidden

    clock.tick(60)

pygame.quit()
