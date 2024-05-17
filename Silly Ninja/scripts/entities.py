import math
import random
import time
import pygame

from scripts.visual_effects import Particle, Projectile, Spark
from scripts.ui.ui_elements import Text


DARK_SLATE_GRAY = pygame.Color("darkslategray")
DARK_GOLDEN_ROD = pygame.Color("darkgoldenrod")


class PhysicsEntity:
	def __init__(self, game, entity_type, pos, size, id="", client_id="solo"):
		self.id = id
		self.client_id = client_id
		self.game = game
		self.type = entity_type
		self.pos = list(pos)
		self.size = size
		self.velocity = [0, 0]
		self.last_movement = (0, 0)
		self.collisions = {"up": False, "down": False, "left": False, "right": False}

		self.animation = None
		self.action = ""
		self.anim_offset = (-3, -3)
		self.facing_left = False


	def rect(self):
		return pygame.Rect(self.pos[0], self.pos[1], self.size[0], self.size[1])


	def set_action(self, action):
		if self.action != action:
			self.action = action
			self.animation = self.game.assets[f"{self.type}/{self.action}"].copy()


	def update(self, tilemap, movement=(0, 0)):
		self.collisions = {"up": False, "down": False, "left": False, "right": False}
		frame_movement = (movement[0] + self.velocity[0], movement[1] + self.velocity[1])

		# Handle collision for the X axis.
		self.pos[0] += frame_movement[0]
		entity_rect = self.rect()
		for rect in tilemap.physics_neighbor_rects(self.pos):
			if entity_rect.colliderect(rect):
				# Moving to the right and collide with something.
				if frame_movement[0] > 0:
					entity_rect.right = rect.left
					self.collisions["right"] = True
				# Moving to the left and collide with something.
				if frame_movement[0] < 0:
					entity_rect.left = rect.right
					self.collisions["left"] = True
				self.pos[0] = entity_rect.x

		# Handle collision for the Y axis.
		self.pos[1] += frame_movement[1]
		entity_rect = self.rect()
		for rect in tilemap.physics_neighbor_rects(self.pos):
			if entity_rect.colliderect(rect):
				# Moving down and collide with something.
				if frame_movement[1] > 0:
					entity_rect.bottom = rect.top
					self.collisions["down"] = True
				# Moving up and collide with something.
				if frame_movement[1] < 0:
					entity_rect.top = rect.bottom
					self.collisions["up"] = True
				self.pos[1] = entity_rect.y

		# Handle gravity.
		self.velocity[1] = min(5, self.velocity[1] + 0.1)
		if self.collisions["down"] or self.collisions["up"]:
			self.velocity[1] = 0

		# Update the animation.
		if movement[0] > 0:
			self.facing_left = False
		if movement[0] < 0:
			self.facing_left = True
		self.animation.update()
		self.last_movement = movement


	def render(self, surface, offset=(0, 0)):
		image_to_render = pygame.transform.flip(self.animation.current_frame_image(), self.facing_left, False)
		surface.blit(image_to_render, (self.pos[0] - offset[0] + self.anim_offset[0],
										self.pos[1] - offset[1] + self.anim_offset[0]))


class Enemy(PhysicsEntity):
	def __init__(self, game, pos, size, id="", client_id="solo"):
		super().__init__(game, "enemy", pos, size, id=id, client_id=client_id)
		self.walking = 0
		self.is_dead = False
		self.fired = False
		self.set_action("idle")


	def __repr__(self):
		return f"Enemy: [ID={self.id:<12}, Client_ID={self.client_id:<9}, IS_DEAD={self.is_dead!s:<5}]"


	def fire_projectile(self, player):
		dist = (player.pos[0] - self.pos[0], player.pos[1] - self.pos[1])
		if abs(dist[1]) < 16:
			if self.facing_left and dist[0] < 0:
				bullet = Projectile(self.game, (self.rect().centerx - 7, self.rect().centery), -1.5, alive_time=0)
				self.game.projectiles.append(bullet)
				self.game.sounds["shoot"].play()
				for i in range(4):
					self.game.sparks.append(Spark(bullet.pos, random.random() - 0.5 + math.pi, random.random() + 2))
			if not self.facing_left and dist[0] > 0:
				bullet = Projectile(self.game, (self.rect().centerx + 7, self.rect().centery), 1.5, alive_time=0)
				self.game.projectiles.append(bullet)
				self.game.sounds["shoot"].play()
				for i in range(4):
					self.game.sparks.append(Spark(bullet.pos, random.random() - 0.5, random.random() + 2))
			return True

		return False


	def check_for_dead(self, player):
		if abs(player.dashing) >= 50:
			if self.rect().colliderect(player.rect()):
				self.game.screenshake = max(self.game.screenshake, 16)
				self.game.sounds["hit"].play()
				for i in range(20, 31):
					angle = random.random() * math.pi * 2
					self.game.sparks.append(Spark(self.rect().center, angle, random.random() * 2 + 2))

					speed = random.random() * 5
					velocity = [math.cos(angle + math.pi) * speed * 0.5, math.sin(angle + math.pi) * speed * 0.5]
					self.game.particles.append(Particle(self.game, "dust", self.rect().center, velocity=velocity, start_frame=random.randint(0, 7)))
				self.game.sparks.append(Spark(self.rect().center, 0, random.random() + 5))
				self.game.sparks.append(Spark(self.rect().center, math.pi, random.random() + 5))

				self.is_dead = True


	def update(self, tilemap, movement=(0, 0), walking=0, facing_left=False):
		# Continue previous movement, if doesn't finish yet.
		if self.walking:
			# Check for flipping against ground and wall tiles in front of the moving direction.
			if tilemap.solid_check((self.rect().centerx + (-7 if self.facing_left else 7), self.pos[1] + 23)):
				if self.collisions["right"] or self.collisions["left"]:
					self.facing_left = not self.facing_left
				else:
					movement = (movement[0] - 0.5 if self.facing_left else 0.5, movement[1])
			else:
				self.facing_left = not self.facing_left
			
			# Fires projectiles at the closest player.
			self.walking = max(self.walking - 1, 0)
			if not self.walking:
				if self.client_id != "solo":
					for player in self.game.entities[:4]:
						if self.fire_projectile(player):
							break
				else:
					self.fire_projectile(self.game.get_main_player())
		
		# Randomize movement, only for the solo and host clients.
		elif random.random() < 0.01 and "client" not in self.client_id:
			self.walking = random.randint(30, 120)
			if random.randint(1, 5) == 1:
				self.facing_left = not self.facing_left
		# Otherwise, assign movement based on the host.
		else:
			self.walking = walking
			self.facing_left = facing_left

		super().update(tilemap, movement=movement)

		# Handle the animation transitions.
		if movement[0] != 0:
			self.set_action("run")
		else:
			self.set_action("idle")

		# Dies if takes damage from the players' dashes or was dead on other clients' machines.
		if self.client_id != "solo":
			for player in self.game.entities[:4]:
				if self.check_for_dead(player):
					break
		else:
			self.check_for_dead(self.game.get_main_player())

		return self.is_dead


	def render(self, surface, offset=(0, 0)):
		super().render(surface, offset=offset)

		# Blit based on the top right of the gun sprite.
		if self.facing_left:
			gun = pygame.transform.flip(self.game.assets["gun"], True, False)
			surface.blit(gun, (self.rect().centerx - 4 - self.game.assets["gun"].get_width() - offset[0],
								self.rect().centery - offset[1]))
		# Blit based on the top left of the gun sprite.
		else:
			surface.blit(self.game.assets["gun"], (self.rect().centerx + 4 - offset[0], self.rect().centery - offset[1]))


class Player(PhysicsEntity):
	def __init__(self, player_name, game, pos, size, id="", client_id="solo"):
		super().__init__(game, "player", pos, size, id=id, client_id=client_id)
		self.air_time = 0
		self.jump_count = 1
		self.dashing = 0

		self.wall_slide = False
		self.jumped = False
		self.died = False

		self.player_name = player_name
		self.name_text = Text(self.player_name, "gamer", self.pos, size=15, color=DARK_SLATE_GRAY)
		self.text_offset = (4, -15)
		self.initialized = False
		self.ready = False

		if self.client_id == "solo":
			self.set_action("idle")


	def __repr__(self):
		return (f"Player: [ID={self.id:<12}, Client_ID={self.client_id:<9}, Nickname={self.player_name:^20}, " +
				f"Initialized={self.initialized!s:<5}, Ready={self.ready!s:<5}]")


	def initialize_client(self, nickname, client_id, player_id, re_initialized=False):
		if not self.initialized or re_initialized:
			self.player_name = nickname
			self.client_id = client_id
			self.id = player_id
			self.name_text.set_text(self.player_name)
			
			if self.id == "main_player":
				self.name_text.color = DARK_GOLDEN_ROD
			
			self.initialized = True
			self.set_action("idle")



	def unregister_client(self, client_index):
		self.player_name = f"unnamed_player_{client_index + 1}"
		self.name_text.set_text(self.player_name)
		self.name_text.color = DARK_SLATE_GRAY
		self.id = f"player_{client_index + 1}"
		self.client_id = ""
		self.initialized = False
		self.ready = False


	def respawn(self, spawn_pos):
		self.pos = list(spawn_pos)
		self.died = False
		self.air_time = 0


	def render_name_tag(self, surface, offset=(0, 0)):
		self.name_text.render(surface, offset=offset)


	def update(self, tilemap, movement=(0, 0), override_pos=(0, 0)):
		super().update(tilemap, movement=movement)
		if tuple(self.pos) != override_pos and override_pos != (0, 0):
			self.pos = list(override_pos)

		self.name_text.update_pos((self.pos[0] + self.text_offset[0], self.pos[1] + self.text_offset[1]))

		# Handle air time and reset when grounded.
		self.air_time += 1
		if self.air_time > 120 and (self.id == "main_player" or self.client_id == "solo"):
			self.died = True
			self.game.dead += 1
			self.game.screenshake = max(self.game.screenshake, 16)

		if self.collisions["down"]:
			self.air_time = 0
			self.jump_count = 1
			self.jumped = False

		# Handle dashing.
		if abs(self.dashing) in {60, 50}:
			# A burst of particles at the beginning and end of a dash.
			for i in range(20):
				angle = random.random() * math.pi * 2
				speed = random.random() * 0.5 + 0.5
				p_velocity = [math.cos(angle) * speed, math.sin(angle) * speed]
				self.game.particles.append(Particle(self.game, "dust", self.rect().center, velocity=p_velocity, start_frame=random.randint(0, 7)))
		
		if self.dashing > 0:  # Dash to the right.
			self.dashing = max(self.dashing - 1, 0)
		else:  # Dash to the left.
			self.dashing = min(self.dashing + 1, 0)
		
		# Generate trail particles.
		if abs(self.dashing) > 50:
			# Get the dash direction and multiply it with an amplitude.
			self.velocity[0] = abs(self.dashing) / self.dashing * 8
			# Make a sudden stop at the end of a dash.
			if abs(self.dashing) == 51:
				self.velocity[0] *= 0.1

			# A stream of particles following the dash.
			p_velocity = [abs(self.dashing) / self.dashing * random.random() * 3, 0]
			self.game.particles.append(Particle(self.game, "dust", self.rect().center, velocity=p_velocity, start_frame=random.randint(0, 7)))

		# Gradually reduce horizontal movement to 0.
		if self.velocity[0] > 0:
			self.velocity[0] = max(self.velocity[0] - 0.1, 0)
		else:
			self.velocity[0] = min(self.velocity[0] + 0.1, 0)

		# Handle wall slide.
		self.wall_slide = False
		if (self.collisions["right"] or self.collisions["left"]) and self.air_time > 7:
			self.wall_slide = True
			self.jumped = False
			self.air_time = 8
			self.velocity[1] = min(self.velocity[1], 0.5)
			self.facing_left = self.collisions["left"]
			self.set_action("wall_slide")
			# Prioritize wall slide animation over the others, so we return here
			return

		# Handle animation transitions.
		if self.air_time > 7 and not self.wall_slide:
			self.set_action("jump")
		elif movement[0] != 0:
			self.set_action("run")
		else:
			self.set_action("idle")



	def render(self, outline_surface, offset=(0, 0)):
		if abs(self.dashing) <= 50:
			super().render(outline_surface, offset=offset)


	def jump(self):
		if not self.died:
			if self.wall_slide:
				self.jumped = True
				if self.facing_left and self.last_movement[0] < 0:
					self.velocity[0] = 2.5
					self.velocity[1] = -2.5
					self.air_time = 8
					self.jump_count = max(self.jump_count - 1, 0)
				elif not self.facing_left and self.last_movement[0] > 0:
					self.velocity[0] = -2.5
					self.velocity[1] = -2.5
					self.air_time = 8
					self.jump_count = max(self.jump_count - 1, 0)
			
			elif self.jump_count:
				self.jumped = True
				self.velocity[1] = -3
				self.jump_count -= 1
				self.air_time = 8

		return self.jumped

		
	def dash(self):
		if not self.dashing and not self.died:
			self.game.sounds["dash"].play()
			self.dashing = -60 if self.facing_left else 60