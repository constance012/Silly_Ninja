import pygame
import sys

from scripts.tilemap import Tilemap, Tile
from scripts.utils import load_images

RENDER_SCALE = 2.0
MAP_ID = "1"

class MapEditor:
	def __init__(self):
		pygame.init()
		pygame.display.set_caption("Map Editor")

		self.clock = pygame.time.Clock()
		self.screen = pygame.display.set_mode((640, 480))
		self.display = pygame.Surface((320, 240))

		# Assets database for tile groups. Values are lists.
		self.assets = {
			"decor": load_images("tiles/decor"),
			"grass": load_images("tiles/grass"),
			"large_decor": load_images("tiles/large_decor"),
			"stone": load_images("tiles/stone"),
			"spawners": load_images("tiles/spawners")
		}

		self.tilemap = Tilemap(self, 16)
		self.tile_list = list(self.assets)
		self.tile_group = 0  # Grass, Decor, Stone,...
		self.tile_variant = 0

		try:
			self.tilemap.load(f"assets/maps/{MAP_ID}.json")
		except FileNotFoundError:
			print("LOAD FAILED! Map file was not found.")

		self.movement = [False, False, False, False]
		self.camera_scroll = [0, 0]

		self.left_clicking = False
		self.right_clicking = False
		self.left_shift = False
		self.left_control = False

		self.on_grid = True


	def run(self):
		while True:
			self.display.fill((150, 150, 150))

			self.camera_scroll[0] += (self.movement[1] - self.movement[0]) * 2
			self.camera_scroll[1] += (self.movement[3] - self.movement[2]) * 2
			render_scroll = (int(self.camera_scroll[0]), int(self.camera_scroll[1]))

			self.tilemap.render(self.display, offset=render_scroll)

			# Get the image of the current tile.
			current_tile_group = self.assets[self.tile_list[self.tile_group]]
			current_tile_image = current_tile_group[self.tile_variant].copy()
			current_tile_image.set_alpha(100)

			# Display the currently selected tile.
			self.display.blit(current_tile_image, (5, 5))

			# Get the mouse position and the position of the tile at the mouse cursor.
			mouse_pos = pygame.mouse.get_pos()
			mouse_pos = (mouse_pos[0] / RENDER_SCALE, mouse_pos[1] / RENDER_SCALE)

			tile_pos = (int((mouse_pos[0] + self.camera_scroll[0]) // self.tilemap.tile_size),
						int((mouse_pos[1] + self.camera_scroll[1]) // self.tilemap.tile_size))
			tile_loc = "{0};{1}".format(tile_pos[0], tile_pos[1])

			# Blit the preview of the current tile to be placed.
			if self.on_grid:
				self.display.blit(current_tile_image, (tile_pos[0] * self.tilemap.tile_size - self.camera_scroll[0],
														tile_pos[1] * self.tilemap.tile_size - self.camera_scroll[1]))
			else:
				self.display.blit(current_tile_image, mouse_pos)

			# Handle placing and deleting tiles on grid.
			if self.left_clicking and self.on_grid:
				self.tilemap.map[tile_loc] = Tile(self.tile_list[self.tile_group], self.tile_variant, tile_pos)
			if self.right_clicking:
				if tile_loc in self.tilemap.map:
					del self.tilemap.map[tile_loc]

				# Handle deleting offgrid tiles.
				for tile in self.tilemap.offgrid_tiles.copy():
					tile_image = self.assets[tile.type][tile.variant]
					tile_rect = pygame.Rect(tile.pos[0] - self.camera_scroll[0], tile.pos[1] - self.camera_scroll[1],
											tile_image.get_width(), tile_image.get_height())
					if tile_rect.collidepoint(mouse_pos):
						self.tilemap.offgrid_tiles.remove(tile)


			for event in pygame.event.get():
				if event.type == pygame.QUIT:
					pygame.quit()
					sys.exit()

				if event.type == pygame.MOUSEBUTTONDOWN:
					if event.button == 1:
						self.left_clicking = True

						# Handle placing offgrid tiles.
						if not self.on_grid:
							offgrid_tile = Tile(self.tile_list[self.tile_group], self.tile_variant,
												(mouse_pos[0] + self.camera_scroll[0], mouse_pos[1] + self.camera_scroll[1]))
							self.tilemap.offgrid_tiles.append(offgrid_tile)
					if event.button == 3:
						self.right_clicking = True
					if self.left_shift:
						# Scroll the mouse wheel up.
						if event.button == 4:
							self.tile_variant = (self.tile_variant - 1) % len(current_tile_group)
						# Scroll the mouse wheel down.
						if event.button == 5:
							self.tile_variant = (self.tile_variant + 1) % len(current_tile_group)
					else:
						if event.button == 4:
							self.tile_group = (self.tile_group - 1) % len(self.tile_list)
							self.tile_variant = 0
						if event.button == 5:
							self.tile_group = (self.tile_group + 1) % len(self.tile_list)
							self.tile_variant = 0

				if event.type == pygame.MOUSEBUTTONUP:
					if event.button == 1:
						self.left_clicking = False
					if event.button == 3:
						self.right_clicking = False

				if event.type == pygame.KEYDOWN:
					if event.key == pygame.K_a:
						self.movement[0] = True
					if event.key == pygame.K_d:
						self.movement[1] = True
					if event.key == pygame.K_w:
						self.movement[2] = True
					if event.key == pygame.K_s:
						self.movement[3] = True
						if self.left_control:
							self.tilemap.save(f"assets/maps/{MAP_ID}.json")
					if self.left_control and event.key == pygame.K_r:
						self.tilemap.ruletile()
					if event.key == pygame.K_g:
						self.on_grid = not self.on_grid
					if event.key == pygame.K_LSHIFT:
						self.left_shift = True
					if event.key == pygame.K_LCTRL:
						self.left_control = True

				if event.type == pygame.KEYUP:
					if event.key == pygame.K_a:
						self.movement[0] = False
					if event.key == pygame.K_d:
						self.movement[1] = False
					if event.key == pygame.K_w:
						self.movement[2] = False
					if event.key == pygame.K_s:
						self.movement[3] = False
					if event.key == pygame.K_LSHIFT:
						self.left_shift = False
					if event.key == pygame.K_LCTRL:
						self.left_control = False

			self.screen.blit(pygame.transform.scale(self.display, self.screen.get_size()), (0, 0))
			pygame.display.update()
			self.clock.tick(60)


if __name__ == '__main__':
	MapEditor().run()