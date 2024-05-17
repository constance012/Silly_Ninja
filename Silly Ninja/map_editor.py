import pygame
import sys
import os
import json
import time

from scripts.tilemap import Tilemap, Tile
from scripts.utils import load_images, fade_out
from scripts.ui.sub_menus import MenuBase
from scripts.ui.ui_elements import Button, BorderedText, Text, InputField


RENDER_SCALE = 2.0
MAP_ID = 0
MAP_PATH = f"assets/maps/{MAP_ID}.json"

WIDTH, HEIGHT = 640, 480
CENTER = WIDTH / 2


class EditorMenu(MenuBase):
	def __init__(self):
		super().__init__()
		pygame.display.set_caption("Map Editor")

		self.editor = MapEditor(MenuBase.clock, MenuBase.screen, MenuBase.normal_display)

		# UI Elements.
		self.title = BorderedText("MAP EDITOR", "retro gaming", (CENTER, 30), size=70, bold=True)
		self.sub_title = Text("----- For Silly Ninja -----", "retro computer", (CENTER, 130), size=15)

		self.error_text = Text("", "retro gaming", (CENTER, 170), size=13, color=pygame.Color("crimson"))
		self.map_id_field = InputField("gamer", (CENTER, 210), (400, 50), placeholder_text="Enter Map ID...")

		self.delete_button = Button("Delete", "gamer", (220, 310), (150, 60), on_click=self.delete_map)
		self.edit_button = Button("Edit", "gamer", (420, 310), (150, 60), on_click=self.edit_map)
		self.quit_button = Button("Quit", "gamer", (CENTER, 390), (150, 60), on_click=self.terminate)


	def run(self):
		while self.running:
			MenuBase.screen.blit(self.background, (0, 0))

			mx, my = pygame.mouse.get_pos()

			# Render titles.
			self.title.render(MenuBase.screen)
			self.sub_title.render(MenuBase.screen)

			# Render the map id field.
			self.error_text.render(MenuBase.screen)
			self.map_id_field.update(mx, my, self.click)
			self.map_id_field.render(MenuBase.screen)

			# Render the delete button.
			self.fade_alpha = self.delete_button.update(MenuBase.screen, self.fade_alpha, mx, my, self.click)
			self.delete_button.render(MenuBase.screen)

			# Render the edit button.
			self.fade_alpha = self.edit_button.update(MenuBase.screen, self.fade_alpha, mx, my, self.click)
			self.edit_button.render(MenuBase.screen)

			# Render the quit button.
			self.fade_alpha = self.quit_button.update(MenuBase.screen, self.fade_alpha, mx, my, self.click)
			self.quit_button.render(MenuBase.screen)

			self.handle_fade_in(MenuBase.screen)

			self.click = False
			for event in pygame.event.get():
				self.handle_events(event)

			pygame.display.update()
			MenuBase.clock.tick(60)


	def edit_map(self):
		try:
			global MAP_ID, MAP_PATH
			MAP_ID = int(self.map_id_field.get_submitted_text())
			MAP_PATH = f"assets/maps/{MAP_ID}.json"
			
			self.editor.load(MAP_ID, self.error_text)
			self.editor.run()
			self.error_text.set_text("")
		
		except ValueError:
			self.error_text.set_text("Map ID must be an Integer")
		except Exception as e:
			self.error_text.set_text(str(e))


	def delete_map(self):
		try:
			global MAP_ID, MAP_PATH
			MAP_ID = int(self.map_id_field.get_submitted_text())
			MAP_PATH = f"assets/maps/{MAP_ID}.json"
			
			if os.path.exists(MAP_PATH):
				os.remove(MAP_PATH)
				self.error_text.set_text(f"DELETED map at \"{MAP_PATH}\".")
			else:
				self.error_text.set_text(f"Map with ID {MAP_ID} doesn't exist.")
		
		except ValueError:
			self.error_text.set_text("Map ID must be an Integer.")
		except Exception as e:
			self.error_text.set_text(str(e))


	def handle_events(self, event):
		super().handle_events(event)
		self.map_id_field.handle_key_pressed(event)


class MapEditor:
	def __init__(self, clock, screen, display):
		self.clock = clock
		self.screen = screen
		self.display = display

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


		self.movement = [False, False, False, False]
		self.camera_scroll = [0, 0]

		self.left_clicking = False
		self.right_clicking = False
		self.shift_held = False
		self.control_held = False

		self.on_grid = True


	def load(self, id, error_text):
		try:
			self.tilemap.load(MAP_PATH)
		except FileNotFoundError:
			error_text.set_text("LOAD FAILED! Map file was not found. Creating an empty map file...")
			time.sleep(2)
			self.create_empty_map(id)


	def create_empty_map(self, id):
		f = open(MAP_PATH, 'x')
		out = {
			"tilemap": {},
			"tile_size": 16,
			"offgrid_tiles": []
		}
		json.dump(out, f, indent=4)
		f.close()
		print(f"Map CREATED at: {MAP_PATH}")
	

	def run(self):
		running = True
		while running:
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
					if self.shift_held:
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
					if event.key == pygame.K_ESCAPE:
						running = False
						fade_out((self.display.get_width(), self.display.get_height()), self.display)
					if event.key == pygame.K_a or event.key == pygame.K_LEFT:
						self.movement[0] = True
					if event.key == pygame.K_d or event.key == pygame.K_RIGHT:
						self.movement[1] = True
					if event.key == pygame.K_w or event.key == pygame.K_UP:
						self.movement[2] = True
					if event.key == pygame.K_s or event.key == pygame.K_DOWN:
						self.movement[3] = True
						print(MAP_ID)
						if self.control_held and event.key == pygame.K_s:
							self.tilemap.save(f"assets/maps/{MAP_ID}.json")
					if self.control_held and event.key == pygame.K_r:
						self.tilemap.ruletile()
					if event.key == pygame.K_g:
						self.on_grid = not self.on_grid
					if event.key == pygame.K_LSHIFT or event.key == pygame.K_RSHIFT:
						self.shift_held = True
					if event.key == pygame.K_LCTRL or event.key == pygame.K_RCTRL:
						self.control_held = True

				if event.type == pygame.KEYUP:
					if event.key == pygame.K_a or event.key == pygame.K_LEFT:
						self.movement[0] = False
					if event.key == pygame.K_d or event.key == pygame.K_RIGHT:
						self.movement[1] = False
					if event.key == pygame.K_w or event.key == pygame.K_UP:
						self.movement[2] = False
					if event.key == pygame.K_s or event.key == pygame.K_DOWN:
						self.movement[3] = False
					if event.key == pygame.K_LSHIFT or event.key == pygame.K_RSHIFT:
						self.shift_held = False
					if event.key == pygame.K_LCTRL or event.key == pygame.K_RCTRL:
						self.control_held = False

			self.screen.blit(pygame.transform.scale(self.display, self.screen.get_size()), (0, 0))
			pygame.display.update()
			self.clock.tick(60)


if __name__ == '__main__':
	EditorMenu().run()