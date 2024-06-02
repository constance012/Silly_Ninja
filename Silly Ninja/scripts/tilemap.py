import pygame
import json


class Tile:
	def __init__(self, t_type, variant, pos):
		self.type = t_type
		self.variant = variant
		self.pos = pos

	def __repr__(self):
		return "Tile[Pos = {0}, Type = {1}, Variant = {2}]".format(self.pos, self.type, self.variant)

	def __dict__(self):
		return {
			"type": self.type,
			"variant": self.variant,
			"pos": self.pos
		}

	def copy(self):
		return Tile(self.type, self.variant, self.pos)


PHYSICS_TILES = {"grass", "stone"}
RULETILE_TYPES = {"grass", "stone"}
RULETILE_MAP = {
	tuple(sorted([(1, 0), (0, 1)])): 0,
	tuple(sorted([(1, 0), (-1, 0), (0, 1)])): 1,
	tuple(sorted([(-1, 0), (0, 1)])): 2,
	tuple(sorted([(-1, 0), (0, -1), (0, 1)])): 3,
	tuple(sorted([(-1, 0), (0, -1)])): 4,
	tuple(sorted([(-1, 0), (1, 0), (0, -1)])): 5,
	tuple(sorted([(1, 0), (0, -1)])): 6,
	tuple(sorted([(1, 0), (0, -1), (0, 1)])): 7,
	tuple(sorted([(1, 0), (-1, 0), (0, 1), (0, -1)])): 8
}


class Tilemap:
	def __init__(self, game, tile_size=16):
		self.game = game
		self.tile_size = tile_size
		self.map = {}  # Tiles which the player can physically collide with.
		self.offgrid_tiles = []  # Background tiles, decorations.
		self.is_empty = True


	def package_as_dict(self, as_json=False):
		out = {
			"tilemap": {tile_loc: self.map[tile_loc].__dict__() for tile_loc in self.map},
			"tile_size": self.tile_size,
			"offgrid_tiles": [tile.__dict__() for tile in self.offgrid_tiles]
		}

		if as_json:
			return json.dumps(out)
		return out


	def save(self, path, override_content=None):
		f = open(path, 'w')

		if override_content is not None:
			override_content = json.loads(override_content)
		else:
			override_content = self.package_as_dict()
		
		json.dump(override_content, f, indent=4)
		f.close()
		print("Map SAVED at: " + path)


	def load(self, path):
		f = open(path, 'r')
		map_data = json.load(f)
		f.close()

		self.map.clear()
		self.offgrid_tiles.clear()

		self.tile_size = map_data["tile_size"]

		for tile_loc in map_data["tilemap"]:
			tile_values = map_data["tilemap"][tile_loc]
			self.map[tile_loc] = Tile(tile_values["type"], tile_values["variant"], tile_values["pos"])

		for offgrid_tile in map_data["offgrid_tiles"]:
			self.offgrid_tiles.append(Tile(offgrid_tile["type"], offgrid_tile["variant"], offgrid_tile["pos"]))

		self.is_empty = False


	def extract(self, id_pairs, keep=False):
		matches = []
		for tile in self.offgrid_tiles.copy():
			if (tile.type, tile.variant) in id_pairs:
				matches.append(tile.copy())
				if not keep:
					self.offgrid_tiles.remove(tile)

		for tile_loc in self.map:
			tile = self.map[tile_loc]
			if (tile.type, tile.variant) in id_pairs:
				matches.append(tile.copy())
				matches[-1].pos = matches[-1].pos.copy()
				mathces[-1].pos[0] *= self.tile_size
				mathces[-1].pos[1] *= self.tile_size
				if not keep:
					del self.map[tile_loc]

		return matches


	def solid_check(self, pos):
		tile_loc = "{0};{1}".format(int(pos[0] // self.tile_size), int(pos[1] // self.tile_size))
		return tile_loc in self.map and self.map[tile_loc].type in PHYSICS_TILES


	def neighbor_tiles(self, pos):
		# Convert back to grid position.
		tile_loc = (int(pos[0] // self.tile_size), int(pos[1] // self.tile_size))
		neighbors = []

		for x in range(-1, 2):
			for y in range(-1, 2):
				check_loc = "{0};{1}".format(tile_loc[0] + x, tile_loc[1] + y)
				if check_loc in self.map:
					neighbors.append(self.map[check_loc])

		return neighbors


	def physics_neighbor_rects(self, pos):
		rects = []
		for tile in self.neighbor_tiles(pos):
			if tile.type in PHYSICS_TILES:
				rect = pygame.Rect(tile.pos[0] * self.tile_size, tile.pos[1] * self.tile_size,
									self.tile_size, self.tile_size)
				rects.append(rect)

		return rects


	# Rule tiles algorithm
	def ruletile(self):
		for tile_loc in self.map:
			tile = self.map[tile_loc]
			neighbors = set()
			for shift in [(1, 0), (-1, 0), (0, -1), (0, 1)]:
				check_loc = "{0};{1}".format(tile.pos[0] + shift[0], tile.pos[1] + shift[1])
				if check_loc in self.map and self.map[check_loc].type == tile.type:
					neighbors.add(shift)

			neighbors = tuple(sorted(neighbors))
			if tile.type in RULETILE_TYPES and neighbors in RULETILE_MAP:
				tile.variant = RULETILE_MAP[neighbors]



	def render(self, surface, offset=(0, 0)):
		for tile in self.offgrid_tiles:
			surface.blit(self.game.assets[tile.type][tile.variant], (tile.pos[0] - offset[0], tile.pos[1] - offset[1]))

		x_start = offset[0] // self.tile_size
		x_end = (offset[0] + surface.get_width()) // self.tile_size + 1
		y_start = offset[1] // self.tile_size
		y_end = (offset[1] + surface.get_height()) // self.tile_size + 1
		for x in range(x_start, x_end):
			for y in range(y_start, y_end):
				loc = "{0};{1}".format(x, y)
				if loc in self.map:
					tile = self.map[loc]
					# Convert grid position to pixel position.
					surface.blit(self.game.assets[tile.type][tile.variant],
								(tile.pos[0] * self.tile_size - offset[0], tile.pos[1] * self.tile_size - offset[1]))