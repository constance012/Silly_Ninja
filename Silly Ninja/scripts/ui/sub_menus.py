import pygame
import socket
import sys
import re
import threading

from scripts.game import GameForHost, GameForClient
from scripts.utils import load_image, show_running_threads
from scripts.ui.ui_elements import Text, Button, InputField, Border
from scripts.socket.server import GameServer
from scripts.socket.client import MAX_CLIENT_COUNT


WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
AZURE4 = pygame.Color("azure4")
DARK_SLATE_GRAY = pygame.Color("darkslategray")
DARK_GOLDEN_ROD = pygame.Color("darkgoldenrod")
FOREST_GREEN = pygame.Color("forestgreen")
FIRE_BRICK = pygame.Color("firebrick")

WIDTH, HEIGHT = 640, 480
CENTER = WIDTH / 2
IP_REGEX = r"^((25[0-5]|(2[0-4]|1\d|[1-9]|)\d)\.?\b){4}$"
PORT_REGEX = r"^[1-9][0-9]{3,4}$"


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


class SubMenuBase(MenuBase):
	def __init__(self):
		super().__init__()
		self.back_button = Button("Back", "gamer", (220, 390), (150, 60), on_click=self.back_out)


	def handle_events(self, event):
		super().handle_events(event)
		if event.type == pygame.KEYDOWN:
			if event.key == pygame.K_ESCAPE:
				self.back_button.click(MenuBase.screen, self.fade_alpha)


class HostMenu(SubMenuBase):
	def __init__(self):
		super().__init__()
		self.default_ip = socket.gethostbyname(socket.gethostname())
		self.default_port = 5050

		self.game = GameForHost(MenuBase.clock, MenuBase.screen, MenuBase.outline_display, MenuBase.normal_display)
		self.server = None
		self.lobby = None

		# UI elements.
		self.title = Text("HOST GAME", "retro gaming", (CENTER, 10), size=70, bold=True)
		self.sub_title = Text("----- Local Area Network (LAN) Only -----", "retro gaming", (CENTER, 90), size=16)

		self.default_ip_text = Text(f"Your default local IP: {self.default_ip}", "retro gaming", (CENTER, 140), size=12)
		self.server_ip_field = InputField("gamer", (CENTER, 160), (400, 50), placeholder_text="Enter Local Host IP...")
		
		self.default_port_text = Text(f"Default Port: {self.default_port}", "retro gaming", (CENTER, 220), size=12)
		self.port_field = InputField("gamer", (CENTER, 240), (400, 50), placeholder_text="Enter Port Number...")

		self.nickname_field = InputField("gamer", (CENTER, 300), (400, 50), placeholder_text="Choose a Nickname...")

		self.status_text = Text("", "retro gaming", (CENTER, 360), size=13, color=pygame.Color("crimson"))

		self.start_button = Button("Start", "gamer", (420, 390), (150, 60), on_click=self.start_hosting, fade_out=False)


	def run(self):
		self.running = True
		self.server_ip_field.set_text(self.default_ip)
		self.port_field.set_text(self.default_port)
		show_running_threads()
		
		while self.running:
			MenuBase.screen.blit(self.background, (0, 0))

			if "[JOINED]" in self.status_text.text:
				self.enter_lobby()
			if self.game.running:
				self.game.run()

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

			# Render the nickname input field.
			self.nickname_field.update(mx, my, self.click)
			self.nickname_field.render(MenuBase.screen)

			# Render the error text.
			self.status_text.render(MenuBase.screen)

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
		nickname = self.nickname_field.get_submitted_text()

		if len(nickname) not in range(3, 16):
			self.status_text.set_text("[ERROR]: Nickname must be from 3 to 15 characters.")

		elif re.match(IP_REGEX, ip) and re.match(PORT_REGEX, port):
			self.status_text.set_text("")
			try:
				print(ip, int(port), nickname)
				self.server = GameServer(ip, port)
				self.game.initialize(self.server, ip, int(port), nickname)

				threading.Thread(target=self.game.start_server, args=(self.status_text, self.set_buttons_interactable)).start()

			except Exception:
				self.status_text.set_text("[FAILED]: Server not found or IP was incorrect! Try again.")
		else:
			self.status_text.set_text("[FORMAT ERROR] IPv4 or Port was invalid (less than 1000)!")


	def enter_lobby(self):
		self.status_text.set_text("")
		del self.lobby
		self.lobby = Lobby(self.game, server=self.server, is_host=True)
		self.lobby.run()


	def set_buttons_interactable(self, state):
		if self.back_button.interactable != state:
			self.back_button.interactable = bool(state)
			self.start_button.interactable = bool(state)


	def handle_events(self, event):
		super().handle_events(event)
		self.server_ip_field.handle_key_pressed(event)
		self.port_field.handle_key_pressed(event)
		self.nickname_field.handle_key_pressed(event)


	def back_out(self):
		super().back_out()
		self.server_ip_field.clear_text()
		self.port_field.clear_text()
		self.status_text.set_text("")


class JoinMenu(SubMenuBase):
	def __init__(self):
		super().__init__()
		self.default_port = 5050

		self.game = GameForClient(MenuBase.clock, MenuBase.screen, MenuBase.outline_display, MenuBase.normal_display)
		self.lobby = None

		# UI elements.
		self.title = Text("JOIN GAME", "retro gaming", (CENTER, 10), size=70, bold=True)
		self.sub_title = Text("----- Local Area Network (LAN) Only -----", "retro gaming", (CENTER, 90), size=16)

		self.default_ip_text = Text("Ask the server's host for their local IP", "retro gaming", (CENTER, 140), size=12)
		self.server_ip_field = InputField("gamer", (CENTER, 160), (400, 50), placeholder_text="Enter Server IP...")
		
		self.default_port_text = Text(f"Default Port: {self.default_port}", "retro gaming", (CENTER, 220), size=12)
		self.port_field = InputField("gamer", (CENTER, 240), (400, 50), placeholder_text="Enter Port Number...")

		self.nickname_field = InputField("gamer", (CENTER, 300), (400, 50), placeholder_text="Choose a Nickname...")

		self.status_text = Text("", "retro gaming", (CENTER, 360), size=13, color=pygame.Color("crimson"))

		self.join_button = Button("Join", "gamer", (420, 390), (150, 60), on_click=self.try_joining, fade_out=False)


	def run(self):
		self.running = True
		self.port_field.set_text(self.default_port)
		show_running_threads()

		while self.running:
			MenuBase.screen.blit(self.background, (0, 0))

			if "[JOINED]" in self.status_text.text:
				self.enter_lobby()
			if self.game.running:
				self.game.run()

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

			# Render the nickname input field.
			self.nickname_field.update(mx, my, self.click)
			self.nickname_field.render(MenuBase.screen)

			# Render the error text.
			self.status_text.render(MenuBase.screen)

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
		ip = self.server_ip_field.get_submitted_text()
		port = self.port_field.get_submitted_text()
		nickname = self.nickname_field.get_submitted_text()

		if len(nickname) not in range(3, 16):
			self.status_text.set_text("[ERROR]: Nickname must be from 3 to 15 characters.")

		elif re.match(IP_REGEX, ip) and re.match(PORT_REGEX, port):
			self.status_text.set_text("")
			try:
				print(ip, int(port), nickname)
				self.game.initialize(ip, int(port), nickname)
				
				threading.Thread(target=self.game.join_lobby, args=(self.status_text, self.set_buttons_interactable)).start()

			except Exception:
				self.status_text.set_text("[FAILED]: Server not found or IP was incorrect! Try again.")
		else:
			self.status_text.set_text("[FORMAT ERROR]: IPv4 or Port was invalid (less than 1000)!")


	def enter_lobby(self):
		self.status_text.set_text("")
		del self.lobby
		self.lobby = Lobby(self.game, server=None, is_host=False)
		self.lobby.run()


	def set_buttons_interactable(self, state):
		if self.back_button.interactable != state:
			self.back_button.interactable = bool(state)
			self.join_button.interactable = bool(state)


	def handle_events(self, event):
		super().handle_events(event)
		self.server_ip_field.handle_key_pressed(event)
		self.port_field.handle_key_pressed(event)
		self.nickname_field.handle_key_pressed(event)


	def back_out(self):
		super().back_out()
		self.server_ip_field.clear_text()
		self.port_field.clear_text()
		self.status_text.set_text("")


class Lobby(SubMenuBase):
	def __init__(self, game_instance, server=None, is_host=False):
		super().__init__()

		self.server = server
		self.is_host = is_host

		self.game_instance = game_instance
		self.game_players = game_instance.entities
		self.connected_players = 0

		# UI Elements.
		self.title = Text("LOBBY", "retro gaming", (CENTER, 10), size=70, bold=True)
		self.sub_title = Text("----- Current Players: 1/4 -----", "retro gaming", (CENTER, 90), size=16)

		self.borders = [
			Border((CENTER, 125), (400, 55), color=AZURE4, line_width=2),
			Border((CENTER, 185), (400, 55), color=AZURE4, line_width=2),
			Border((CENTER, 245), (400, 55), color=AZURE4, line_width=2),
			Border((CENTER, 305), (400, 55), color=AZURE4, line_width=2)
		]

		self.player_names = [
			Text("EMPTY SLOT", "gamer", (CENTER, 120), size=50, color=DARK_SLATE_GRAY),
			Text("EMPTY SLOT", "gamer", (CENTER, 180), size=50, color=DARK_SLATE_GRAY),
			Text("EMPTY SLOT", "gamer", (CENTER, 240), size=50, color=DARK_SLATE_GRAY),
			Text("EMPTY SLOT", "gamer", (CENTER, 300), size=50, color=DARK_SLATE_GRAY)
		]

		self.player_status = [
			Text("--- Disconnected ---", "retro gaming", (CENTER, 160), size=14, color=DARK_SLATE_GRAY),
			Text("--- Disconnected ---", "retro gaming", (CENTER, 220), size=14, color=DARK_SLATE_GRAY),
			Text("--- Disconnected ---", "retro gaming", (CENTER, 280), size=14, color=DARK_SLATE_GRAY),
			Text("--- Disconnected ---", "retro gaming", (CENTER, 340), size=14, color=DARK_SLATE_GRAY)
		]

		self.status_text = Text("", "retro gaming", (CENTER, 365), size=13, color=pygame.Color("crimson"))

		if self.is_host:
			self.launch_button = Button("Launch", "gamer", (420, 390), (150, 60), on_click=self.launch, fade_out=False)
		else:
			self.back_button.pos = (CENTER, 390)
			self.back_button.display_text.pos = (CENTER, 390)


	def run(self):
		self.running = True
		print("Lobby running...")

		while self.running:
			self.running = self.game_instance.connected and not self.game_instance.running

			MenuBase.screen.blit(self.background, (0, 0))

			mx, my = pygame.mouse.get_pos()

			# Render title.
			self.title.render(MenuBase.screen)
			self.sub_title.set_text(f"----- Current Players: {self.connected_players}/{MAX_CLIENT_COUNT} -----")
			self.sub_title.render(MenuBase.screen)

			# Update and Render player slots.
			self.update_player_slots()
			for i in range(MAX_CLIENT_COUNT):
				self.borders[i].render(MenuBase.screen)
				self.player_names[i].render(MenuBase.screen)
				self.player_status[i].render(MenuBase.screen)

			# Render the status text.
			self.status_text.render(MenuBase.screen)

			# Render the launch button, only for the host lobby.
			if self.is_host:
				self.fade_alpha = self.launch_button.update(MenuBase.screen, self.fade_alpha, mx, my, self.click)
				self.launch_button.render(MenuBase.screen)

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


	def update_player_slots(self):
		for i in range(MAX_CLIENT_COUNT):
			player = self.game_players[i]
			# Update player slots when new players joined.
			if player.initialized:
				self.borders[i].color = FOREST_GREEN if player.ready else FIRE_BRICK
				if self.player_names[i].text != player.player_name:
					self.player_names[i].set_text(player.player_name)
					self.player_names[i].color = DARK_GOLDEN_ROD if player.id == "main_player" else DARK_SLATE_GRAY
					self.player_status[i].set_text("--- Host ---" if player.client_id == "host" else "--- Connected ---")
					self.connected_players += 1
			
			# Or reset slots when players left.
			elif not player.initialized and self.player_names[i].text != "EMPTY SLOT":
				self.borders[i].color = AZURE4
				self.player_names[i].set_text("EMPTY SLOT")
				self.player_names[i].color = DARK_SLATE_GRAY
				self.player_status[i].set_text("--- Disconnected ---")
				self.connected_players -= 1


	def launch(self):
		if all(player.ready for player in self.game_players[:self.connected_players]):
			threading.Thread(target=self.game_instance.launch_session, args=(self.status_text, self.set_buttons_interactable)).start()
		else:
			self.status_text.set_text("[WAITING]: Players joining, can not launch.")


	def set_buttons_interactable(self, state):
		if self.back_button.interactable != state:
			self.back_button.interactable = bool(state)
			if self.is_host:
				self.launch_button.interactable = bool(state)


	def back_out(self):
		super().back_out()
		
		if self.is_host and self.server is not None:
			self.server.shutdown()
		else:
			self.game_instance.disconnect_from_server()