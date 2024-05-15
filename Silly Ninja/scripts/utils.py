import pygame
import os
import threading

BASE_IMAGE_PATH = "assets/images/"

def load_image(path):
	image = pygame.image.load(BASE_IMAGE_PATH + path).convert()
	image.set_colorkey((0, 0, 0))
	return image


def load_images(path):
	images = []
	
	for image_name in sorted(os.listdir(BASE_IMAGE_PATH + path)):
		images.append(load_image(path + "/" + image_name))
	
	return images


# Fading out effect.
def fade_out(WINDOW_SIZE, draw_surface, color=(255, 255, 255)):
	fade_out = pygame.Surface(WINDOW_SIZE)  # Input a tuple.
	fade_out.fill(color)

	for alpha in range(0, 256):  # Set opaque value.
		fade_out.set_alpha(alpha)
		draw_surface.blit(fade_out, (0, 0))
		pygame.display.update()
		pygame.time.delay(4)  # Each loop time has 4ms delay.


def show_running_threads():
	for thread in threading.enumerate():
		print(thread.name)


if __name__ == '__main__':
	print(len("cstt"))