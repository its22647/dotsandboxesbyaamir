import os
import pygame

pygame.init()

# Auto-Detect User's Monitor Screen Resolution
info = pygame.display.Info()
screen_res_w = info.current_w if info.current_w > 0 else 1366
screen_res_h = info.current_h if info.current_h > 0 else 768

# Safe Proportional Window Size
DEFAULT_WIDTH = max(800, min(1180, int(screen_res_w * 0.86)))
DEFAULT_HEIGHT = max(560, min(740, int(screen_res_h * 0.84)))

DEVELOPER_NAME = "Muhammad Aamir Bakhsh"
APP_TITLE = "DOTS & BOXES"
APP_VERSION = "v1.0.0"
APP_BUILD_TYPE = "Desktop Standalone Edition"

# Premium Dark Studio Themes
THEMES = {
    "Cyber Slate": {
        "bg_top": (15, 23, 42),
        "bg_bottom": (9, 14, 26),
        "grid_dots_base": (28, 40, 64),
        "panel": (22, 30, 48),
        "panel_surface": (16, 22, 36),
        "panel_border": (45, 62, 94),
        "dot": (245, 247, 250),
        "grid_idle": (32, 44, 70),
        "text_main": (248, 250, 252),
        "text_sub": (148, 163, 184),
        "accent": (0, 210, 255)
    },
    "Obsidian Luxe": {
        "bg_top": (18, 18, 24),
        "bg_bottom": (9, 9, 13),
        "grid_dots_base": (35, 35, 46),
        "panel": (26, 26, 36),
        "panel_surface": (18, 18, 26),
        "panel_border": (52, 52, 70),
        "dot": (252, 252, 252),
        "grid_idle": (38, 38, 52),
        "text_main": (255, 255, 255),
        "text_sub": (160, 160, 175),
        "accent": (255, 195, 0)
    },
    "Emerald Studio": {
        "bg_top": (10, 24, 20),
        "bg_bottom": (5, 13, 11),
        "grid_dots_base": (20, 42, 36),
        "panel": (16, 36, 30),
        "panel_surface": (11, 26, 22),
        "panel_border": (32, 68, 56),
        "dot": (238, 255, 250),
        "grid_idle": (24, 50, 42),
        "text_main": (245, 255, 250),
        "text_sub": (140, 180, 165),
        "accent": (16, 255, 130)
    },
    "Midnight Blue": {
        "bg_top": (13, 17, 34),
        "bg_bottom": (7, 9, 20),
        "grid_dots_base": (26, 36, 60),
        "panel": (20, 26, 46),
        "panel_surface": (14, 18, 34),
        "panel_border": (40, 54, 88),
        "dot": (242, 246, 255),
        "grid_idle": (30, 40, 68),
        "text_main": (250, 252, 255),
        "text_sub": (140, 155, 185),
        "accent": (99, 102, 241)
    }
}

AVAILABLE_COLORS = [
    {"name": "Crimson", "rgb": (255, 51, 102)},
    {"name": "Electric Cyan", "rgb": (0, 210, 255)},
    {"name": "Neon Emerald", "rgb": (16, 255, 130)},
    {"name": "Solar Gold", "rgb": (255, 195, 0)},
    {"name": "Ultra Violet", "rgb": (175, 75, 255)},
    {"name": "Blaze Orange", "rgb": (255, 110, 0)},
    {"name": "Hot Pink", "rgb": (255, 25, 150)},
    {"name": "Lime Acid", "rgb": (195, 255, 0)}
]

FONT_CACHE = {}

def get_scaled_font(size, bold=False):
    font_name = "Segoe UI" if os.name == 'nt' else "Helvetica Neue"
    key = (font_name, max(9, int(size)), bold)
    if key not in FONT_CACHE:
        FONT_CACHE[key] = pygame.font.SysFont(font_name, key[1], bold=bold)
    return FONT_CACHE[key]