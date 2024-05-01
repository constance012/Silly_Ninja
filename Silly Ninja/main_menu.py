import pygame
import sys

from game import Game
from scripts.utils import load_image
from scripts.ui_elements import Button, Text, BorderedText, InputField


WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
YELLOW = (145, 136, 32)

WIDTH, HEIGHT = 640, 480
CENTER = WIDTH / 2


class MainMenu:
	def __init__(self):
		pygame.init()
		pygame.display.set_caption("Silly Ninja")

		self.clock = pygame.time.Clock()
		self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
		self.outline_display = pygame.Surface((WIDTH / 2, HEIGHT / 2), pygame.SRCALPHA)  # Outline display
		self.normal_display = pygame.Surface((WIDTH / 2, HEIGHT / 2))  # Normal display

		self.background = pygame.transform.scale(load_image("background.png"), self.screen.get_size())
		self.fade_alpha = 0
		self.click = False

		# Game
		self.game = Game(self.clock, self.screen, self.outline_display, self.normal_display)

		# UI Elements.
		self.title = BorderedText("SILLY NINJA", "retro gaming", (CENTER, 30), size=70, bold=True)
		self.version_text = Text("----- Beta v0.9 -----", "retro computer", (CENTER, 130), size=15)

		self.solo_button = Button("Solo", "gamer", (CENTER, 180), (150, 60), on_click=self.game.run)
		self.join_button = Button("Join", "gamer", (CENTER, 250), (150, 60))
		self.host_button = Button("Host", "gamer", (CENTER, 320), (150, 60))
		self.quit_button = Button("Quit", "gamer", (CENTER, 390), (150, 60), on_click=self.terminate)


	def run(self):
		pygame.mixer.music.load("assets/music.wav")
		pygame.mixer.music.set_volume(0.6)
		pygame.mixer.music.play(-1)
		
		while True:
			self.screen.blit(self.background, (0, 0))

			mx, my = pygame.mouse.get_pos()

			# Render the title.
			self.title.render(self.screen)
			self.version_text.render(self.screen)

			# Render the solo button.
			self.fade_alpha = self.solo_button.update(self.screen, self.fade_alpha, mx, my, self.click)
			self.solo_button.render(self.screen)

			# Render the join button.
			self.fade_alpha = self.join_button.update(self.screen, self.fade_alpha, mx, my, self.click)
			self.join_button.render(self.screen)

			# Render the host button.
			self.fade_alpha = self.host_button.update(self.screen, self.fade_alpha, mx, my, self.click)
			self.host_button.render(self.screen)

			# Render the quit button.
			self.quit_button.update(self.screen, self.fade_alpha, mx, my, self.click)
			self.quit_button.render(self.screen)

			# Handle the fade-in effect.
			if self.fade_alpha > 0:
				if self.fade_alpha == 255:
					fade_in = pygame.Surface((WIDTH, HEIGHT))
					fade_in.fill(BLACK)

				fade_in.set_alpha(self.fade_alpha)
				self.screen.blit(fade_in, (0, 0))
				self.fade_alpha -= 15

			# Events handling.
			self.click = False
			for event in pygame.event.get():
				if event.type == pygame.QUIT:
					self.terminate()
				if event.type == pygame.MOUSEBUTTONDOWN:
					if event.button == 1:  # When the LMB is clicked.
						self.click = True

			
			pygame.display.update()
			self.clock.tick(60)


	def terminate(self):
		pygame.quit()
		sys.exit()


if __name__ == "__main__":
	MainMenu().run()