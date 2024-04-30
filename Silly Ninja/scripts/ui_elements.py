import pygame

from scripts.utils import fade_out


WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
YELLOW = (213, 219, 86)
DARK_BLUE = (74, 113, 128)


class UIBase:
	def __init__(self, pos, size):
		self.x = pos[0]
		self.y = pos[1]
		self.width = size[0]
		self.height = size[1]
		self.rect = pygame.Rect(self.x, self.y, self.width, self.height)


	def get_pos(self):
		return (self.x, self.y)


	def get_size(self):
		return (self.width, self.height)


	def get_rect(self):
		return self.rect


	@staticmethod
	def draw_text(text_obj, x, y, surface):
		text_rect = text_obj.get_rect()  # Get the font's Rect object.
		text_rect.midtop = (x, y)  # Bind the rect position to top center.
		surface.blit(text_obj, text_rect)  # Blit it on the screen.


	@staticmethod
	def draw_rect(rect, draw_surface, x, y, color=(0, 0, 0), line_width=0):
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
		self.text_obj = self.font.render(text, True, color)
		super().__init__(pos, self.text_obj.get_size())

		self.text = text
		self.size = size
		self.color = color
		self.bold = bold


	def render(self, surface, override_color=None):
		text_color = self.color if override_color is None else override_color
		self.text_obj = self.font.render(self.text, False, text_color)
		UIBase.draw_text(self.text_obj, self.x, self.y, surface)


class BorderedText(Text):
	def __init__(self, text, font_name, pos, size=20, color=BLACK, bold=False):
		super().__init__(text, font_name, pos, size=size, color=color, bold=bold)
		self.border = Border(pos, (self.width + 20, self.height), color=self.color)


	def render(self, surface, override_color=None):
		self.border.render(surface)
		super().render(surface, override_color)


class Button(UIBase):
	def __init__(self, display_text, font_name, pos, size, on_click=None, text_offset=0):
		super().__init__(pos, size)
		self.on_click = on_click

		self.text_color = WHITE
		self.rect_color = DARK_BLUE

		self.display_text = Text(display_text, font_name, pos, size=self.height + text_offset)


	def update(self, surface, fade_alpha, mx, my, click):
		if self.rect.collidepoint((mx, my)):
			self.text_color = YELLOW
			if click and self.on_click is not None:
				fade_out((surface.get_width(), surface.get_height()), surface, color=BLACK)
				self.on_click()
				fade_alpha = 255
		else:
			self.text_color = WHITE

		return fade_alpha


	def render(self, surface):
		UIBase.draw_rect(self.rect, surface, self.x, self.y, color=self.rect_color)
		self.display_text.render(surface, override_color=self.text_color)