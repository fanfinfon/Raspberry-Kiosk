import pygame
import os

pygame.init()
screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
pygame.mouse.set_visible(False)

# Folder for synced images
image_folder = "/home/caglar/Desktop/Kiosk/images"

def load_images():
    return [os.path.join(image_folder, f) for f in os.listdir(image_folder) 
            if f.endswith((".png", ".jpg", ".jpeg", ".webp"))]

images = load_images()
running = True
index = 0
clock = pygame.time.Clock()
image_time = 0
delay = 5000  # 5000 ms = 5 seconds

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE or event.key == pygame.K_q:
                running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            running = False

    # Reload image list in case sync script updated files
    if index == 0:
        images = load_images()

    # Current time in ms
    current_time = pygame.time.get_ticks()

    if images and (current_time - image_time > delay):
        img = pygame.image.load(images[index])
        img_w, img_h = img.get_size()
        screen_w, screen_h = screen.get_size()

        # Scale proportionally
        scale = min(screen_w / img_w, screen_h / img_h)
        new_w, new_h = int(img_w * scale), int(img_h * scale)
        img = pygame.transform.smoothscale(img, (new_w, new_h))

        # Center the image
        x = (screen_w - new_w) // 2
        y = (screen_h - new_h) // 2

        # Clear background
        screen.fill((0, 0, 0))
        screen.blit(img, (x, y))
        pygame.display.flip()

        # Next image
        index = (index + 1) % len(images)
        image_time = current_time

    clock.tick(60)  # Keep loop at 60 FPS

pygame.quit()
