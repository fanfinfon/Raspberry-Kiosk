# kiosk.py
import pygame
import os
from dotenv import load_dotenv
from redis_sync import sync_images

# Load env variables
load_dotenv()

image_folder = os.getenv("IMAGE_FOLDER", "./images")
delay = int(os.getenv("IMAGE_DELAY", 5000))       # ms
update_delay = int(os.getenv("UPDATE_DELAY", 300000))  # ms

pygame.init()
screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
pygame.mouse.set_visible(False)

images = sync_images(image_folder)

running = True
index = 0
clock = pygame.time.Clock()

image_time = 0
update_time = 0

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_ESCAPE, pygame.K_q):
                running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            running = False

    current_time = pygame.time.get_ticks()

    if images and current_time - image_time > delay:
        img = pygame.image.load(images[index])
        img_w, img_h = img.get_size()
        screen_w, screen_h = screen.get_size()

        scale = min(screen_w / img_w, screen_h / img_h)
        new_w, new_h = int(img_w * scale), int(img_h * scale)

        img = pygame.transform.smoothscale(img, (new_w, new_h))
        x = (screen_w - new_w) // 2
        y = (screen_h - new_h) // 2

        screen.fill((0, 0, 0))
        screen.blit(img, (x, y))
        pygame.display.flip()

        index = (index + 1) % len(images)
        image_time = current_time

    if current_time - update_time > update_delay:
        images = sync_images(image_folder)
        index = 0
        update_time = current_time

    clock.tick(60)

pygame.quit()
