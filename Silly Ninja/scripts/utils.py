import pygame
import os

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