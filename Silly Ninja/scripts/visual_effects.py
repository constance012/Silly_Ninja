import math
import pygame

class Projectile:
	def __init__(self, game, pos, direction, alive_time=0):
		self.game = game
		self.pos = list(pos)
		self.direction = direction
		self.alive_time = alive_time

	def update(self):
		self.pos[0] += self.direction
		self.alive_time += 1

	def render(self, surface, offset=(0, 0)):
		img = self.game.assets["projectile"]
		surface.blit(img, (self.pos[0] - img.get_width() / 2 - offset[0],
							self.pos[1] - img.get_height() / 2 - offset[1]))


class Spark:
	def __init__(self, pos, angle, speed):
		self.pos = list(pos)
		self.angle = angle
		self.speed = speed

	def update(self):
		self.pos[0] += math.cos(self.angle) * self.speed
		self.pos[1] += math.sin(self.angle) * self.speed

		self.speed = max(self.speed - 0.1, 0)
		return not self.speed

	def render(self, surface, offset=(0, 0)):
		render_points = [
			(self.pos[0] + math.cos(self.angle) * self.speed * 3 - offset[0], self.pos[1] + math.sin(self.angle) * self.speed * 3 - offset[1]),
			(self.pos[0] + math.cos(self.angle + math.pi * 0.5) * self.speed * 0.5 - offset[0], self.pos[1] + math.sin(self.angle + math.pi * 0.5) * self.speed * 0.5 - offset[1]),
			(self.pos[0] + math.cos(self.angle + math.pi) * self.speed * 3 - offset[0], self.pos[1] + math.sin(self.angle + math.pi) * self.speed * 3 - offset[1]),
			(self.pos[0] + math.cos(self.angle - math.pi * 0.5) * self.speed * 0.5 - offset[0], self.pos[1] + math.sin(self.angle - math.pi * 0.5) * self.speed * 0.5 - offset[1])
		]
		pygame.draw.polygon(surface, (255, 255, 255), render_points)


class Particle:
	def __init__(self, game, p_type, pos, velocity=[0, 0], start_frame=0):
		self.game = game
		self.type = p_type
		self.pos = list(pos)
		self.velocity = list(velocity)
		self.animation = self.game.assets["particle/" + self.type].copy()
		self.animation.frame = start_frame


	def update(self):
		kill = self.animation.done

		self.pos[0] += self.velocity[0]
		self.pos[1] += self.velocity[1]

		self.animation.update()
		return kill


	def render(self, surface, offset=(0, 0)):
		image = self.animation.current_frame_image()

		# Render at the center of the image.
		surface.blit(image, (self.pos[0] - offset[0] + image.get_width() // 2,
							self.pos[1] - offset[1] + image.get_height() // 2))