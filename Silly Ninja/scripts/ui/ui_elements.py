import pygame

from scripts.utils import fade_out


WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
TAN2 = pygame.Color("tan2")
STEEL_BLUE_2 = pygame.Color("steelblue2")
STEEL_BLUE_4 = pygame.Color("steelblue4")
DODGER_BLUE_2 = pygame.Color("dodgerblue2")
DODGER_BLUE_4 = pygame.Color("dodgerblue4")


class UIBase:
	def __init__(self, pos, size):
		self.x = pos[0]
		self.y = pos[1]
		self._width = size[0]
		self.height = size[1]
		self.rect = pygame.Rect(self.x, self.y, self.width, self.height)

	@property
	def width(self):
		return self._width

	@width.setter
	def width(self, value):
		self._width = value
		self.rect.w = value

	def get_pos(self):
		return (self.x, self.y)

	def get_size(self):
		return (self.width, self.height)

	def get_rect(self):
		return self.rect

	@staticmethod
	def draw_text(text_obj, x, y, surface, alpha=255):
		text_obj.set_alpha(alpha)
		text_rect = text_obj.get_rect()  # Get the font's Rect object.
		text_rect.midtop = (x, y)  # Bind the rect position to top center.
		surface.blit(text_obj, text_rect)  # Blit it on the screen.

	@staticmethod
	def draw_rect(rect, draw_surface, x, y, color=BLACK, line_width=0):
		rect.midtop = (x, y)
		pygame.draw.rect(draw_surface, color, rect, line_width)


class Border(UIBase):
	def __init__(self, pos, size, color=BLACK, line_width=5):
		super().__init__(pos, size)
		self.color = color
		self.line_width = line_width


	def render(self, surface):
		UIBase.draw_rect(self.rect, surface, self.x, self.y, color=self.color, line_width=self.line_width)


class Text(UIBase):
	def __init__(self, text, font_name, pos, size=20, color=BLACK, bold=False):
		self.font = pygame.font.SysFont(font_name, size, bold)
		self.text_obj = self.font.render(text, False, color)
		super().__init__(pos, self.text_obj.get_size())

		self.text = text
		self.size = size
		self.color = color
		self.bold = bold


	def render(self, surface, override_color=None, alpha=255):
		text_color = self.color if override_color is None else override_color
		self.text_obj = self.font.render(self.text, False, text_color)
		self.width = self.text_obj.get_width()
		UIBase.draw_text(self.text_obj, self.x, self.y, surface, alpha=alpha)


	def __repr__(self):
		return self.text


class BorderedText(Text):
	def __init__(self, text, font_name, pos, size=20, text_color=BLACK, bold=False, border_color=BLACK, line_width=5):
		super().__init__(text, font_name, pos, size=size, color=text_color, bold=bold)
		self.border = Border(pos, (self.width + 20, self.height), color=border_color, line_width=line_width)


	def render(self, surface, override_color=None):
		self.border.render(surface)
		super().render(surface, override_color)


class Button(UIBase):
	def __init__(self, display_text, font_name, pos, size, on_click=None, text_offset=0):
		super().__init__(pos, size)
		self.on_click = on_click

		self.text_color = WHITE
		self.rect_color = STEEL_BLUE_4
		self.expand_speed = 3

		self.display_text = Text(display_text, font_name, pos, size=self.height + text_offset)


	def reset_state(self):
		self.rect.w = self.width
		self.text_color = WHITE


	def update(self, surface, fade_alpha, mx, my, click):
		if self.rect.collidepoint((mx, my)):
			self.text_color = TAN2
			self.rect.w = min(self.width + 20, self.rect.w + self.expand_speed)

			if click and self.on_click is not None:
				fade_out((surface.get_width(), surface.get_height()), surface, color=BLACK)
				self.reset_state()
				self.on_click()
				fade_alpha = 255
		
		elif self.rect.w != self.width:
			self.text_color = WHITE
			self.rect.w = max(self.width, self.rect.w - self.expand_speed)

		return fade_alpha


	def render(self, surface):
		UIBase.draw_rect(self.rect, surface, self.x, self.y, color=self.rect_color)
		self.display_text.render(surface, override_color=self.text_color)


class InputField(UIBase):
	def __init__(self, font_name, pos, size, placeholder_text="", on_submit=None, text_offset=0):
		super().__init__(pos, size)
		self.on_submit = on_submit

		self.color = pygame.Color(DODGER_BLUE_4)
		self.placeholder_text = placeholder_text
		self.display_text = Text(self.placeholder_text, font_name, pos, size=self.height + text_offset, color=WHITE)

		self.active = False


	def update(self, mx, my, click):
		if click:
			if self.rect.collidepoint((mx, my)):
				self.active = not self.active
				if self.active and self.display_text.text == self.placeholder_text:
					self.display_text.text = ""
			else:
				self.active = False
				if self.display_text.text == "":
					self.display_text.text = self.placeholder_text

		self.color = DODGER_BLUE_2 if self.active else DODGER_BLUE_4

		# Resize the box if the text grows beyond the initial width.
		self.rect.w = max(self.width, self.display_text.width + 20)


	def handle_key_pressed(self, event):
		if self.active and event.type == pygame.KEYDOWN:
			if event.key == pygame.K_RETURN:
				if self.on_submit is not None:
					self.on_submit()
				print(self.display_text)
			
			elif event.key == pygame.K_BACKSPACE:
				self.display_text.text = self.display_text.text[:-1]
			
			else:
				self.display_text.text += event.unicode


	def render(self, surface):
		alpha = 80 if self.display_text.text == self.placeholder_text else 255
		UIBase.draw_rect(self.rect, surface, self.x, self.y, color=self.color)
		self.display_text.render(surface, alpha=alpha)


	def get_submitted_text(self):
		return self.display_text.text


	def clear_text(self):
		self.display_text.text = self.placeholder_text