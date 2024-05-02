import pygame
import socket
import sys

from scripts.utils import load_image
from scripts.ui.ui_elements import Text, Button, InputField
from scripts.socket.server import SocketServer


WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

WIDTH, HEIGHT = 640, 480
CENTER = WIDTH / 2


class MenuBase:
	# Class variables.
	clock = pygame.time.Clock()
	screen = pygame.display.set_mode((WIDTH, HEIGHT))

	outline_display = pygame.Surface((WIDTH / 2, HEIGHT / 2), pygame.SRCALPHA)  # Outline display
	normal_display = pygame.Surface((WIDTH / 2, HEIGHT / 2))  # Normal display
	fade_in = pygame.Surface((WIDTH, HEIGHT))


	def __init__(self):
		pygame.init()

		self.background = pygame.transform.scale(load_image("background.png"), MenuBase.screen.get_size())
		self.fade_alpha = 0
		self.click = False
		self.running = True


	def handle_fade_in(self, surface):
		# Handle the fade-in effect.
		if self.fade_alpha > 0:
			if self.fade_alpha == 255:
				MenuBase.fade_in.fill(BLACK)

			MenuBase.fade_in.set_alpha(self.fade_alpha)
			surface.blit(MenuBase.fade_in, (0, 0))
			self.fade_alpha -= 15


	def handle_events(self, event):
		if event.type == pygame.QUIT:
			self.terminate()
		if event.type == pygame.MOUSEBUTTONDOWN:
			if event.button == 1:  # When the LMB is clicked.
				self.click = True


	def terminate(self):
		pygame.quit()
		sys.exit()


	def back_out(self):
		self.running = False


class HostMenu(MenuBase):
	def __init__(self):
		super().__init__()

		# UI elements.
		self.title = Text("HOST GAME", "retro gaming", (CENTER, 30), size=70, bold=True)
		self.sub_title = Text("----- Local Area Network (LAN) Only -----", "retro gaming", (CENTER, 110), size=16)

		default_ip = socket.gethostbyname(socket.gethostname())
		self.default_ip_text = Text(f"Your default local IP: {default_ip}", "retro gaming", (CENTER, 170), size=12)
		self.server_ip_field = InputField("gamer", (CENTER, 190), (400, 50), placeholder_text="Enter Local Host IP...")
		
		self.default_port_text = Text("Default Port: 5050", "retro gaming", (CENTER, 270), size=12)
		self.port_field = InputField("gamer", (CENTER, 290), (400, 50), placeholder_text="Enter Port Number...")

		self.back_button = Button("Back", "gamer", (220, 390), (150, 60), on_click=self.back_out)
		self.start_button = Button("Start", "gamer", (420, 390), (150, 60), on_click=self.start_hosting)

		self.server = None


	def run(self):
		self.running = True
		while self.running:
			MenuBase.screen.blit(self.background, (0, 0))

			mx, my = pygame.mouse.get_pos()

			# Render titles.
			self.title.render(MenuBase.screen)
			self.sub_title.render(MenuBase.screen)

			# Render the server ip input field.
			self.default_ip_text.render(MenuBase.screen)
			self.server_ip_field.update(mx, my, self.click)
			self.server_ip_field.render(MenuBase.screen)

			# Render the port number input field.
			self.default_port_text.render(MenuBase.screen)
			self.port_field.update(mx, my, self.click)
			self.port_field.render(MenuBase.screen)

			# Render the start button.
			self.fade_alpha = self.start_button.update(MenuBase.screen, self.fade_alpha, mx, my, self.click)
			self.start_button.render(MenuBase.screen)

			# Render the back button.
			self.fade_alpha = self.back_button.update(MenuBase.screen, self.fade_alpha, mx, my, self.click)
			self.back_button.render(MenuBase.screen)

			# Handle the fade int effect.
			self.handle_fade_in(MenuBase.screen)

			# Handle events.
			self.click = False
			for event in pygame.event.get():
				self.handle_events(event)

			pygame.display.update()
			MenuBase.clock.tick(60)


	def start_hosting(self):
		ip = self.server_ip_field.get_submitted_text()
		port = self.port_field.get_submitted_text()

		try:
			self.server = SocketServer(ip, port)
			self.server.start_server()
		except Exception:
			print("IP or port was invalid! Try again.")


	def handle_events(self, event):
		super().handle_events(event)
		if event.type == pygame.KEYDOWN:
			self.server_ip_field.handle_key_pressed(event)
			self.port_field.handle_key_pressed(event)


	def back_out(self):
		super().back_out()
		self.server_ip_field.clear_text()
		self.port_field.clear_text()


class JoinMenu(MenuBase):
	def __init__(self):
		super().__init__()

		# UI elements.
		self.title = Text("JOIN GAME", "retro gaming", (CENTER, 30), size=70, bold=True)
		self.sub_title = Text("----- Local Area Network (LAN) Only -----", "retro gaming", (CENTER, 110), size=16)

		self.default_ip_text = Text("Ask the server's host for their local IP", "retro gaming", (CENTER, 170), size=12)
		self.server_ip_field = InputField("gamer", (CENTER, 190), (400, 50), placeholder_text="Enter Server IP...")
		
		self.default_port_text = Text("Default Port: 5050", "retro gaming", (CENTER, 270), size=12)
		self.port_field = InputField("gamer", (CENTER, 290), (400, 50), placeholder_text="Enter Port Number...")

		self.back_button = Button("Back", "gamer", (220, 390), (150, 60), on_click=self.back_out)
		self.join_button = Button("Join", "gamer", (420, 390), (150, 60), on_click=self.try_joining)


	def run(self):
		self.running = True
		while self.running:
			MenuBase.screen.blit(self.background, (0, 0))

			mx, my = pygame.mouse.get_pos()

			# Render title.
			self.title.render(MenuBase.screen)
			self.sub_title.render(MenuBase.screen)

			# Render the server ip input field.
			self.default_ip_text.render(MenuBase.screen)
			self.server_ip_field.update(mx, my, self.click)
			self.server_ip_field.render(MenuBase.screen)

			# Render the port number input field.
			self.default_port_text.render(MenuBase.screen)
			self.port_field.update(mx, my, self.click)
			self.port_field.render(MenuBase.screen)

			# Render the start button.
			self.fade_alpha = self.join_button.update(MenuBase.screen, self.fade_alpha, mx, my, self.click)
			self.join_button.render(MenuBase.screen)

			# Render the back button.
			self.fade_alpha = self.back_button.update(MenuBase.screen, self.fade_alpha, mx, my, self.click)
			self.back_button.render(MenuBase.screen)

			# Handle the fade int effect.
			self.handle_fade_in(MenuBase.screen)

			# Handle events.
			self.click = False
			for event in pygame.event.get():
				self.handle_events(event)

			pygame.display.update()
			MenuBase.clock.tick(60)


	def try_joining(self):
		pass


	def handle_events(self, event):
		super().handle_events(event)
		if event.type == pygame.KEYDOWN:
			self.server_ip_field.handle_key_pressed(event)
			self.port_field.handle_key_pressed(event)


	def back_out(self):
		super().back_out()
		self.server_ip_field.clear_text()
		self.port_field.clear_text()