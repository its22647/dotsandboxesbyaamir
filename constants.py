import os
import pygame

pygame.init()

info = pygame.display.Info()
screen_res_w = info.current_w if info.current_w > 0 else 1366
screen_res_h = info.current_h if info.current_h > 0 else 768

DEFAULT_WIDTH = max(900, min(1240, int(screen_res_w * 0.88)))
DEFAULT_HEIGHT = max(600, min(780, int(screen_res_h * 0.86)))

DEVELOPER_NAME = "Muhammad Aamir Bakhsh"
APP_TITLE = "DOTS & BOXES"
APP_VERSION = "v2.0.0 Arcade Studio"
APP_BUILD_TYPE = "Next-Gen Engine"

THEMES = {
    "Cyber Slate": {
        "bg_top": (10, 15, 30),
        "bg_bottom": (5, 8, 16),
        "grid_dots_base": (22, 32, 54),
        "panel": (16, 22, 38),
        "panel_surface": (11, 16, 28),
        "panel_border": (35, 50, 80),
        "dot": (240, 245, 255),
        "grid_idle": (25, 38, 64),
        "text_main": (255, 255, 255),
        "text_sub": (148, 163, 184),
        "accent": (0, 225, 255)
    },
    "Obsidian Luxe": {
        "bg_top": (16, 16, 22),
        "bg_bottom": (8, 8, 12),
        "grid_dots_base": (30, 30, 42),
        "panel": (22, 22, 32),
        "panel_surface": (14, 14, 22),
        "panel_border": (45, 45, 65),
        "dot": (255, 255, 255),
        "grid_idle": (35, 35, 50),
        "text_main": (255, 255, 255),
        "text_sub": (160, 160, 175),
        "accent": (255, 180, 0)
    },
    "Emerald Studio": {
        "bg_top": (8, 20, 16),
        "bg_bottom": (4, 10, 8),
        "grid_dots_base": (18, 38, 32),
        "panel": (14, 30, 25),
        "panel_surface": (9, 20, 16),
        "panel_border": (28, 60, 50),
        "dot": (230, 255, 245),
        "grid_idle": (22, 48, 40),
        "text_main": (245, 255, 250),
        "text_sub": (130, 175, 160),
        "accent": (16, 255, 130)
    },
    "Midnight Blue": {
        "bg_top": (11, 15, 32),
        "bg_bottom": (5, 7, 18),
        "grid_dots_base": (22, 30, 56),
        "panel": (17, 23, 42),
        "panel_surface": (11, 15, 30),
        "panel_border": (36, 48, 82),
        "dot": (240, 245, 255),
        "grid_idle": (26, 36, 64),
        "text_main": (250, 252, 255),
        "text_sub": (140, 155, 185),
        "accent": (120, 90, 255)
    }
}

AVAILABLE_COLORS = [
    {"name": "Crimson Red", "rgb": (255, 45, 85)},
    {"name": "Electric Cyan", "rgb": (0, 210, 255)},
    {"name": "Neon Emerald", "rgb": (16, 255, 130)},
    {"name": "Solar Gold", "rgb": (255, 185, 0)},
    {"name": "Ultra Violet", "rgb": (185, 85, 255)},
    {"name": "Blaze Orange", "rgb": (255, 115, 0)},
    {"name": "Hot Pink", "rgb": (255, 20, 145)},
    {"name": "Acid Lime", "rgb": (195, 255, 0)}
]

FONT_CACHE = {}

def get_scaled_font(size, bold=False):
    font_name = "Segoe UI" if os.name == 'nt' else "Helvetica Neue"
    key = (font_name, max(9, int(size)), bold)
    if key not in FONT_CACHE:
        FONT_CACHE[key] = pygame.font.SysFont(font_name, key[1], bold=bold)
    return FONT_CACHE[key]