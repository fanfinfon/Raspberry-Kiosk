import pygame
import os
import time

pygame.init()
screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
pygame.mouse.set_visible(False)

# Folder for synced images
image_folder = "/home/caglar/Desktop/Kiosk/images"

def load_images():
    """Return a list of image paths in the image folder."""
    return [os.path.join(image_folder, f) for f in os.listdir(image_folder)
            if f.lower().endswith((".png", ".jpg", ".jpeg", ".webp", ".heic"))]

def fade_in(surface, duration=0.5):
    """Smooth fade-in for an image surface."""
    clock = pygame.time.Clock()
    fade_steps = int(duration * 60)  # assuming 60 fps
    for alpha in range(0, 256, int(255 / fade_steps) or 1):
        surface.set_alpha(alpha)
        screen.fill((0, 0, 0))
        screen.blit(surface, surface.get_rect(center=screen.get_rect().center))
        pygame.display.flip()
        clock.tick(60)
    surface.set_alpha(255)  # ensure fully opaque at the end

images = load_images()
running = True
index = 0
clock = pygame.time.Clock()
image_time = 0
delay = 15000  # 15 seconds per image

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_ESCAPE, pygame.K_q):
                running = False

    # Reload image list occasionally
    if index == 0:
        images = load_images()

    # Current time in ms
    current_time = pygame.time.get_ticks()

    if images and (current_time - image_time > delay):
        try:
            img = pygame.image.load(images[index])
            img_w, img_h = img.get_size()
            screen_w, screen_h = screen.get_size()

            # Scale proportionally
            scale = min(screen_w / img_w, screen_h / img_h)
            new_w, new_h = int(img_w * scale), int(img_h * scale)
            img = pygame.transform.smoothscale(img, (new_w, new_h))

            # Convert to display format and fade in smoothly
            img = img.convert()
            fade_in(img)

            # Reset timer and go to next image
            index = (index + 1) % len(images)
            image_time = current_time

            # Keep cursor hidden (redundant safety)
            pygame.mouse.set_visible(False)

        except Exception as e:
            print(f"Error loading image {images[index]}: {e}")
            index = (index + 1) % len(images)
            continue

    clock.tick(60)

pygame.quit()
