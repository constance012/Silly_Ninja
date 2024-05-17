import pygame

from scripts.game import GameSolo
from scripts.ui.ui_elements import Button, Text, BorderedText
from scripts.ui.sub_menus import MenuBase, HostMenu, JoinMenu


WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

WIDTH, HEIGHT = 640, 480
CENTER = WIDTH / 2


class MainMenu(MenuBase):
	def __init__(self):
		super().__init__()
		pygame.display.set_caption("Silly Ninja")

		# Game and sub menus.
		self.game_solo = GameSolo(MenuBase.clock, MenuBase.screen, MenuBase.outline_display, MenuBase.normal_display)

		self.host_menu = HostMenu()
		self.join_menu = JoinMenu()

		# UI Elements.
		self.title = BorderedText("SILLY NINJA", "retro gaming", (CENTER, 30), size=70, bold=True)
		self.version_text = Text("----- Beta v0.9 -----", "retro computer", (CENTER, 130), size=15)

		self.solo_button = Button("Solo", "gamer", (CENTER, 180), (150, 60), on_click=self.game_solo.run)
		self.join_button = Button("Join", "gamer", (CENTER, 250), (150, 60), on_click=self.join_menu.run)
		self.host_button = Button("Host", "gamer", (CENTER, 320), (150, 60), on_click=self.host_menu.run)
		self.quit_button = Button("Quit", "gamer", (CENTER, 390), (150, 60), on_click=self.terminate, fade_out=False)


	def run(self):
		pygame.mixer.music.load("assets/music.wav")
		pygame.mixer.music.set_volume(0.6)
		pygame.mixer.music.play(-1)
		
		while self.running:
			MenuBase.screen.blit(self.background, (0, 0))

			mx, my = pygame.mouse.get_pos()

			# Render the title.
			self.title.render(MenuBase.screen)
			self.version_text.render(MenuBase.screen)

			# Render the solo button.
			self.fade_alpha = self.solo_button.update(MenuBase.screen, self.fade_alpha, mx, my, self.click)
			self.solo_button.render(MenuBase.screen)

			# Render the join button.
			self.fade_alpha = self.join_button.update(MenuBase.screen, self.fade_alpha, mx, my, self.click)
			self.join_button.render(MenuBase.screen)

			# Render the host button.
			self.fade_alpha = self.host_button.update(MenuBase.screen, self.fade_alpha, mx, my, self.click)
			self.host_button.render(MenuBase.screen)

			# Render the quit button.
			self.quit_button.update(MenuBase.screen, self.fade_alpha, mx, my, self.click)
			self.quit_button.render(MenuBase.screen)

			# Handle the fade in effect.
			self.handle_fade_in(MenuBase.screen)
			
			# Handle events.
			self.click = False
			for event in pygame.event.get():
				self.handle_events(event)

			pygame.display.update()
			MenuBase.clock.tick(60)


if __name__ == "__main__":
	MainMenu().run()