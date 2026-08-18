import os
import sys
import math
import time
import ctypes
from ctypes import wintypes
import pygame
from constants import (
    DEFAULT_WIDTH, DEFAULT_HEIGHT, DEVELOPER_NAME, APP_TITLE,
    APP_VERSION, APP_BUILD_TYPE, THEMES, AVAILABLE_COLORS,
    get_scaled_font
)
from board import GameBoard

pygame.init()
pygame.key.set_repeat(280, 30)

# Window Setup
screen = pygame.display.set_mode((DEFAULT_WIDTH, DEFAULT_HEIGHT), pygame.RESIZABLE)
pygame.display.set_caption(APP_TITLE)
clock = pygame.time.Clock()

# Win32 Constants for Clean Borderless Fullscreen
GWL_STYLE = -16
WS_POPUP = 0x80000000
WS_VISIBLE = 0x10000000
WS_OVERLAPPEDWINDOW = 0x00CF0000
SWP_FRAMECHANGED = 0x0020
SWP_SHOWWINDOW = 0x0040
HWND_TOP = 0

is_fullscreen = False
saved_rect = wintypes.RECT(100, 100, 100 + DEFAULT_WIDTH, 100 + DEFAULT_HEIGHT)

current_state = "WELCOME"
show_about = False
is_paused = False
confirm_modal = None

selected_theme_key = "Cyber Slate"
num_players = 2
grid_size = 4
available_grids = [3, 4, 5, 6, 7, 8, 12]
player_names = ["Player 1", "Player 2", "Player 3", "Player 4", "Player 5"]
player_color_indices = [0, 1, 2, 3, 4]

active_input_idx = None
select_all = False

board = None
drag_start_dot = None

# Per-Turn Timer (15.0s)
TURN_DURATION = 15.0
time_remaining = TURN_DURATION
last_timer_update = 0.0

global_tick = 0
welcome_intro_timer = 0
about_type_timer = 0

bg_cache = None
bg_cache_size = (0, 0)
bg_cache_theme = ""

def get_player_rgb(player_idx):
    c_idx = player_color_indices[player_idx]
    return AVAILABLE_COLORS[c_idx]["rgb"]

def get_wave_rgb(offset_timer):
    r = int(127 + 127 * math.sin(offset_timer * 0.05))
    g = int(127 + 127 * math.sin(offset_timer * 0.05 + 2.094))
    b = int(127 + 127 * math.sin(offset_timer * 0.05 + 4.188))
    return (r, g, b)

def toggle_true_borderless_fullscreen():
    global is_fullscreen, saved_rect, bg_cache
    bg_cache = None
    
    if os.name == 'nt':
        try:
            hwnd = pygame.display.get_wm_info()['window']
            user32 = ctypes.windll.user32
            
            if not is_fullscreen:
                user32.GetWindowRect(hwnd, ctypes.byref(saved_rect))
                screen_w = user32.GetSystemMetrics(0)
                screen_h = user32.GetSystemMetrics(1)
                user32.SetWindowLongW(hwnd, GWL_STYLE, WS_POPUP | WS_VISIBLE)
                user32.SetWindowPos(
                    hwnd, HWND_TOP, 0, 0, screen_w, screen_h,
                    SWP_FRAMECHANGED | SWP_SHOWWINDOW
                )
                is_fullscreen = True
            else:
                user32.SetWindowLongW(hwnd, GWL_STYLE, WS_OVERLAPPEDWINDOW | WS_VISIBLE)
                w = saved_rect.right - saved_rect.left
                h = saved_rect.bottom - saved_rect.top
                user32.SetWindowPos(
                    hwnd, HWND_TOP, saved_rect.left, saved_rect.top, w, h,
                    SWP_FRAMECHANGED | SWP_SHOWWINDOW
                )
                is_fullscreen = False
        except Exception:
            pass

def draw_animated_background(w, h):
    global bg_cache, bg_cache_size, bg_cache_theme
    theme = THEMES[selected_theme_key]

    if bg_cache is None or bg_cache_size != (w, h) or bg_cache_theme != selected_theme_key:
        bg_cache = pygame.Surface((w, h))
        for y in range(0, h, 6):
            ratio = y / h
            r = int(theme["bg_top"][0] * (1 - ratio) + theme["bg_bottom"][0] * ratio)
            g = int(theme["bg_top"][1] * (1 - ratio) + theme["bg_bottom"][1] * ratio)
            b = int(theme["bg_top"][2] * (1 - ratio) + theme["bg_bottom"][2] * ratio)
            pygame.draw.rect(bg_cache, (r, g, b), (0, y, w, 6))

        step = max(36, int(min(w, h) * 0.052))
        for gx in range(0, w, step):
            for gy in range(0, h, step):
                pygame.draw.circle(bg_cache, theme["grid_dots_base"], (gx, gy), 1)

        bg_cache_size = (w, h)
        bg_cache_theme = selected_theme_key

    screen.blit(bg_cache, (0, 0))

    glow_surf = pygame.Surface((w, h), pygame.SRCALPHA)
    t = global_tick * 0.015
    acc = theme["accent"]
    
    orb1_x = int(w * 0.25 + math.sin(t * 0.5) * 80)
    orb1_y = int(h * 0.35 + math.cos(t * 0.4) * 60)
    orb2_x = int(w * 0.75 + math.cos(t * 0.45) * 90)
    orb2_y = int(h * 0.65 + math.sin(t * 0.55) * 70)

    pygame.draw.circle(glow_surf, (acc[0], acc[1], acc[2], 22), (orb1_x, orb1_y), int(min(w, h) * 0.32))
    pygame.draw.circle(glow_surf, (acc[0], acc[1], acc[2], 18), (orb2_x, orb2_y), int(min(w, h) * 0.38))
    screen.blit(glow_surf, (0, 0))

def draw_welcome_screen(w, h):
    global welcome_intro_timer
    welcome_intro_timer += 1
    draw_animated_background(w, h)
    theme = THEMES[selected_theme_key]

    hero_w = min(int(w * 0.72), 650)
    hero_h = min(int(h * 0.72), 460)
    hero_rect = pygame.Rect((w - hero_w) // 2, (h - hero_h) // 2 - 10, hero_w, hero_h)
    
    pygame.draw.rect(screen, theme["panel"], hero_rect, border_radius=22)
    pygame.draw.rect(screen, theme["panel_border"], hero_rect, width=2, border_radius=22)

    title_font = get_scaled_font(hero_h * 0.13, bold=True)
    t_surf = title_font.render(APP_TITLE, True, theme["accent"])
    screen.blit(t_surf, (hero_rect.centerx - t_surf.get_width() // 2, hero_rect.top + int(hero_h * 0.12)))

    anim_rgb = get_wave_rgb(global_tick)
    dev_font = get_scaled_font(hero_h * 0.052, bold=True)
    dev_txt = dev_font.render(f"Developed by {DEVELOPER_NAME}", True, anim_rgb)
    
    badge_rect = pygame.Rect(hero_rect.centerx - (dev_txt.get_width() // 2) - 20, hero_rect.top + int(hero_h * 0.32), dev_txt.get_width() + 40, dev_txt.get_height() + 14)
    pygame.draw.rect(screen, theme["panel_surface"], badge_rect, border_radius=14)
    pygame.draw.rect(screen, anim_rgb, badge_rect, width=1, border_radius=14)
    screen.blit(dev_txt, (hero_rect.centerx - dev_txt.get_width() // 2, badge_rect.centery - dev_txt.get_height() // 2))

    btn_w = int(hero_w * 0.50)
    btn_h = int(hero_h * 0.13)

    play_btn = pygame.Rect(hero_rect.centerx - btn_w // 2, hero_rect.top + int(hero_h * 0.54), btn_w, btn_h)
    pygame.draw.rect(screen, (255, 51, 102), play_btn, border_radius=12)
    pt = get_scaled_font(btn_h * 0.45, bold=True).render("PLAY NOW", True, (255, 255, 255))
    screen.blit(pt, (play_btn.centerx - pt.get_width() // 2, play_btn.centery - pt.get_height() // 2))

    # Action Row: About & Exit Game
    btn_row_y = hero_rect.top + int(hero_h * 0.73)
    abt_w = int(btn_w * 0.46)
    
    abt_btn = pygame.Rect(hero_rect.centerx - abt_w - 8, btn_row_y, abt_w, int(btn_h * 0.75))
    pygame.draw.rect(screen, theme["panel_surface"], abt_btn, border_radius=10)
    pygame.draw.rect(screen, theme["panel_border"], abt_btn, width=1, border_radius=10)
    at = get_scaled_font(abt_btn.height * 0.42, bold=True).render("About", True, theme["text_main"])
    screen.blit(at, (abt_btn.centerx - at.get_width() // 2, abt_btn.centery - at.get_height() // 2))

    exit_btn = pygame.Rect(hero_rect.centerx + 8, btn_row_y, abt_w, int(btn_h * 0.75))
    pygame.draw.rect(screen, theme["panel_surface"], exit_btn, border_radius=10)
    pygame.draw.rect(screen, (255, 51, 102), exit_btn, width=1, border_radius=10)
    et = get_scaled_font(exit_btn.height * 0.42, bold=True).render("Exit", True, (255, 51, 102))
    screen.blit(et, (exit_btn.centerx - et.get_width() // 2, exit_btn.centery - et.get_height() // 2))

    v_txt = get_scaled_font(min(w, h) * 0.018).render(f"{APP_VERSION} • {APP_BUILD_TYPE}", True, theme["text_sub"])
    screen.blit(v_txt, (w // 2 - v_txt.get_width() // 2, h - int(h * 0.035)))

def draw_about_dialog(w, h):
    global about_type_timer
    about_type_timer += 1
    theme = THEMES[selected_theme_key]

    overlay = pygame.Surface((w, h), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 215))
    screen.blit(overlay, (0, 0))

    modal_w, modal_h = min(int(w * 0.75), 560), min(int(h * 0.70), 390)
    rect = pygame.Rect((w - modal_w)//2, (h - modal_h)//2, modal_w, modal_h)

    pygame.draw.rect(screen, theme["panel"], rect, border_radius=18)
    pygame.draw.rect(screen, theme["panel_border"], rect, width=2, border_radius=18)

    t = get_scaled_font(modal_h * 0.08, bold=True).render("ABOUT APPLICATION", True, theme["accent"])
    screen.blit(t, (rect.centerx - t.get_width()//2, rect.top + int(modal_h * 0.08)))

    c_box = pygame.Rect(rect.left + 30, rect.top + int(modal_h * 0.22), modal_w - 60, int(modal_h * 0.32))
    pygame.draw.rect(screen, theme["panel_surface"], c_box, border_radius=12)
    pygame.draw.rect(screen, theme["panel_border"], c_box, width=1, border_radius=12)

    l1 = get_scaled_font(modal_h * 0.044, bold=True).render("DEVELOPED BY", True, (16, 255, 130))
    screen.blit(l1, (c_box.centerx - l1.get_width()//2, c_box.top + int(c_box.height * 0.18)))

    full_name = DEVELOPER_NAME
    visible_chars = min(len(full_name), max(1, about_type_timer // 3))
    
    font_name = get_scaled_font(modal_h * 0.078, bold=True)
    total_w = font_name.size(full_name[:visible_chars])[0]
    start_x = c_box.centerx - total_w // 2
    name_y = c_box.top + int(c_box.height * 0.50)

    curr_x = start_x
    for i, ch in enumerate(full_name[:visible_chars]):
        ch_color = get_wave_rgb(global_tick + (i * 6))
        ch_surf = font_name.render(ch, True, ch_color)
        screen.blit(ch_surf, (curr_x, name_y))
        curr_x += font_name.size(ch)[0]

    meta_box = pygame.Rect(rect.left + 30, rect.top + int(modal_h * 0.58), modal_w - 60, int(modal_h * 0.20))
    pygame.draw.rect(screen, theme["panel_surface"], meta_box, border_radius=8)

    m1 = get_scaled_font(modal_h * 0.042).render(f"Version:  {APP_VERSION}", True, theme["text_main"])
    m2 = get_scaled_font(modal_h * 0.042).render(f"Edition:  {APP_BUILD_TYPE}", True, theme["text_sub"])
    screen.blit(m1, (meta_box.left + 20, meta_box.top + 12))
    screen.blit(m2, (meta_box.left + 20, meta_box.top + 36))

    btn = pygame.Rect(rect.centerx - 70, rect.bottom - int(modal_h * 0.14), 140, int(modal_h * 0.09))
    pygame.draw.rect(screen, (255, 51, 102), btn, border_radius=8)
    cl = get_scaled_font(btn.height * 0.45, bold=True).render("CLOSE", True, (255, 255, 255))
    screen.blit(cl, (btn.centerx - cl.get_width()//2, btn.centery - cl.get_height()//2))

def draw_confirmation_dialog(w, h):
    theme = THEMES[selected_theme_key]
    overlay = pygame.Surface((w, h), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 220))
    screen.blit(overlay, (0, 0))

    modal_w, modal_h = min(int(w * 0.75), 450), min(int(h * 0.48), 230)
    rect = pygame.Rect((w - modal_w)//2, (h - modal_h)//2, modal_w, modal_h)

    pygame.draw.rect(screen, theme["panel"], rect, border_radius=16)
    pygame.draw.rect(screen, (255, 51, 102), rect, width=2, border_radius=16)

    if confirm_modal == 'QUIT':
        q_title = "EXIT GAME?"
        q_desc = "Are you sure you want to close the game?"
    elif confirm_modal == 'RESTART':
        q_title = "RESTART MATCH?"
        q_desc = "Current game progress will be lost."
    else:
        q_title = "EXIT TO MAIN MENU?"
        q_desc = "Current game progress will be lost."
    
    t_s = get_scaled_font(modal_h * 0.12, bold=True).render(q_title, True, (255, 255, 255))
    d_s = get_scaled_font(modal_h * 0.075).render(q_desc, True, theme["text_sub"])
    screen.blit(t_s, (rect.centerx - t_s.get_width()//2, rect.top + int(modal_h * 0.18)))
    screen.blit(d_s, (rect.centerx - d_s.get_width()//2, rect.top + int(modal_h * 0.38)))

    btn_w = int(modal_w * 0.38)
    btn_h = int(modal_h * 0.18)

    yes_btn = pygame.Rect(rect.left + 30, rect.bottom - btn_h - 18, btn_w, btn_h)
    pygame.draw.rect(screen, (255, 51, 102), yes_btn, border_radius=10)
    yt = get_scaled_font(btn_h * 0.45, bold=True).render("Yes, Confirm", True, (255, 255, 255))
    screen.blit(yt, (yes_btn.centerx - yt.get_width()//2, yes_btn.centery - yt.get_height()//2))

    no_btn = pygame.Rect(rect.right - 30 - btn_w, rect.bottom - btn_h - 18, btn_w, btn_h)
    pygame.draw.rect(screen, theme["panel_border"], no_btn, border_radius=10)
    nt = get_scaled_font(btn_h * 0.45, bold=True).render("Cancel", True, (255, 255, 255))
    screen.blit(nt, (no_btn.centerx - nt.get_width()//2, no_btn.centery - nt.get_height()//2))

def draw_pause_dialog(w, h):
    theme = THEMES[selected_theme_key]
    overlay = pygame.Surface((w, h), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 215))
    screen.blit(overlay, (0, 0))

    modal_w, modal_h = min(int(w * 0.75), 440), min(int(h * 0.42), 210)
    rect = pygame.Rect((w - modal_w)//2, (h - modal_h)//2, modal_w, modal_h)

    pygame.draw.rect(screen, theme["panel"], rect, border_radius=18)
    pygame.draw.rect(screen, theme["accent"], rect, width=2, border_radius=18)

    pt = get_scaled_font(modal_h * 0.18, bold=True).render("GAME PAUSED", True, theme["accent"])
    screen.blit(pt, (rect.centerx - pt.get_width()//2, rect.top + int(modal_h * 0.22)))

    btn_w = int(modal_w * 0.52)
    btn_h = int(modal_h * 0.24)
    resume_btn = pygame.Rect(rect.centerx - btn_w // 2, rect.bottom - btn_h - 22, btn_w, btn_h)
    pygame.draw.rect(screen, (16, 255, 130), resume_btn, border_radius=10)
    rt = get_scaled_font(btn_h * 0.46, bold=True).render("RESUME GAME", True, (0, 0, 0))
    screen.blit(rt, (resume_btn.centerx - rt.get_width()//2, resume_btn.centery - rt.get_height()//2))

def draw_menu(w, h):
    draw_animated_background(w, h)
    theme = THEMES[selected_theme_key]

    title_font = get_scaled_font(min(w, h) * 0.046, bold=True)
    t = title_font.render(APP_TITLE, True, theme["text_main"])
    screen.blit(t, (w // 2 - t.get_width() // 2, int(h * 0.020)))

    anim_rgb = get_wave_rgb(global_tick)
    dev_font = get_scaled_font(min(w, h) * 0.022, bold=True)
    d = dev_font.render(f"Developed by {DEVELOPER_NAME}", True, anim_rgb)
    screen.blit(d, (w // 2 - d.get_width() // 2, int(h * 0.072)))

    # Header Action Buttons: About & Exit Game
    abt_w, abt_h = max(70, int(w * 0.075)), max(28, int(h * 0.042))
    
    abt_btn = pygame.Rect(w - (abt_w * 2) - int(w * 0.04) - 8, int(h * 0.024), abt_w, abt_h)
    pygame.draw.rect(screen, theme["panel"], abt_btn, border_radius=8)
    pygame.draw.rect(screen, theme["panel_border"], abt_btn, width=1, border_radius=8)
    abt_txt = get_scaled_font(abt_h * 0.45, bold=True).render("About", True, theme["text_main"])
    screen.blit(abt_txt, (abt_btn.centerx - abt_txt.get_width()//2, abt_btn.centery - abt_txt.get_height()//2))

    exit_btn = pygame.Rect(w - abt_w - int(w * 0.03), int(h * 0.024), abt_w, abt_h)
    pygame.draw.rect(screen, theme["panel"], exit_btn, border_radius=8)
    pygame.draw.rect(screen, (255, 51, 102), exit_btn, width=1, border_radius=8)
    exit_txt = get_scaled_font(abt_h * 0.45, bold=True).render("Exit", True, (255, 51, 102))
    screen.blit(exit_txt, (exit_btn.centerx - exit_txt.get_width()//2, exit_btn.centery - exit_txt.get_height()//2))

    card_w = min(int(w * 0.94), 980)
    card_h = min(int(h * 0.82), 620)
    card = pygame.Rect((w - card_w)//2, int(h * 0.12), card_w, card_h)
    pygame.draw.rect(screen, theme["panel"], card, border_radius=18)
    pygame.draw.rect(screen, theme["panel_border"], card, width=2, border_radius=18)

    # 1. Themes Selector
    t_y = card.top + int(card_h * 0.030)
    lbl1 = get_scaled_font(card_h * 0.030, bold=True).render("ARENA THEME", True, theme["text_main"])
    screen.blit(lbl1, (card.left + 30, t_y))
    
    t_keys = list(THEMES.keys())
    btn_w = (card_w - 60 - ((len(t_keys)-1)*10)) // len(t_keys)
    for i, tname in enumerate(t_keys):
        b = pygame.Rect(card.left + 30 + (i*(btn_w+10)), t_y + int(card_h * 0.040), btn_w, int(card_h * 0.058))
        sel = (selected_theme_key == tname)
        pygame.draw.rect(screen, theme["accent"] if sel else theme["panel_surface"], b, border_radius=8)
        pygame.draw.rect(screen, theme["panel_border"], b, width=1, border_radius=8)
        bt = get_scaled_font(b.height * 0.42, bold=True).render(tname, True, (0, 0, 0) if sel else theme["text_main"])
        screen.blit(bt, (b.centerx - bt.get_width()//2, b.centery - bt.get_height()//2))

    # 2. Players & Grid Matrix Row
    p_y = card.top + int(card_h * 0.155)
    lbl2 = get_scaled_font(card_h * 0.030, bold=True).render("PLAYERS", True, theme["text_main"])
    screen.blit(lbl2, (card.left + 30, p_y))
    for i, cnt in enumerate([2, 3, 4, 5]):
        b = pygame.Rect(card.left + 30 + (i * 76), p_y + int(card_h * 0.040), 70, int(card_h * 0.058))
        sel = (num_players == cnt)
        pygame.draw.rect(screen, (16, 255, 130) if sel else theme["panel_surface"], b, border_radius=8)
        pygame.draw.rect(screen, theme["panel_border"], b, width=1, border_radius=8)
        bt = get_scaled_font(b.height * 0.45, bold=True).render(f"{cnt}P", True, (0, 0, 0) if sel else theme["text_main"])
        screen.blit(bt, (b.centerx - bt.get_width()//2, b.centery - bt.get_height()//2))

    lbl3 = get_scaled_font(card_h * 0.030, bold=True).render("GRID MATRIX", True, theme["text_main"])
    screen.blit(lbl3, (card.left + 360, p_y))
    for i, sz in enumerate(available_grids):
        b = pygame.Rect(card.left + 360 + (i * 68), p_y + int(card_h * 0.040), 62, int(card_h * 0.058))
        sel = (grid_size == sz)
        pygame.draw.rect(screen, (255, 195, 0) if sel else theme["panel_surface"], b, border_radius=8)
        pygame.draw.rect(screen, theme["panel_border"], b, width=1, border_radius=8)
        bt = get_scaled_font(b.height * 0.45, bold=True).render(f"{sz}x{sz}", True, (0, 0, 0) if sel else theme["text_main"])
        screen.blit(bt, (b.centerx - bt.get_width()//2, b.centery - bt.get_height()//2))

    # 3. Player Identities & Color Selector Cards
    n_y = card.top + int(card_h * 0.285)
    lbl4 = get_scaled_font(card_h * 0.028, bold=True).render("PLAYER IDENTITIES & COLOR ALLOCATION", True, theme["text_sub"])
    screen.blit(lbl4, (card.left + 30, n_y))

    row_h = int(card_h * 0.085)
    for i in range(num_players):
        row_y = n_y + int(card_h * 0.038) + (i * (row_h + 5))
        row_rect = pygame.Rect(card.left + 30, row_y, card_w - 60, row_h)
        pygame.draw.rect(screen, theme["panel_surface"], row_rect, border_radius=10)
        pygame.draw.rect(screen, theme["panel_border"], row_rect, width=1, border_radius=10)

        in_box = pygame.Rect(row_rect.left + 12, row_rect.top + 5, int(row_rect.width * 0.34), row_rect.height - 10)
        is_focus = (active_input_idx == i)
        curr_p_rgb = get_player_rgb(i)

        pygame.draw.rect(screen, (10, 14, 24), in_box, border_radius=6)
        pygame.draw.rect(screen, curr_p_rgb if is_focus else theme["panel_border"], in_box, width=2 if is_focus else 1, border_radius=6)
        pygame.draw.circle(screen, curr_p_rgb, (in_box.left + 14, in_box.centery), 5)

        raw_str = player_names[i]
        if is_focus and select_all:
            ts = get_scaled_font(in_box.height * 0.45, bold=True).render(raw_str, True, (255, 255, 255))
            sel_r = pygame.Rect(in_box.left + 26, in_box.centery - ts.get_height()//2, ts.get_width() + 4, ts.get_height())
            pygame.draw.rect(screen, (0, 210, 255), sel_r, border_radius=4)
            screen.blit(ts, (in_box.left + 28, in_box.centery - ts.get_height()//2))
        else:
            disp = raw_str + ("|" if is_focus else "")
            ts = get_scaled_font(in_box.height * 0.45, bold=True).render(disp, True, theme["text_main"])
            screen.blit(ts, (in_box.left + 28, in_box.centery - ts.get_height()//2))

        col_start_x = in_box.right + 25
        c_swatch_size = int(row_rect.height * 0.55)
        for c_idx, c_obj in enumerate(AVAILABLE_COLORS):
            cx = col_start_x + (c_idx * (c_swatch_size + 8))
            cy = row_rect.centery - c_swatch_size // 2
            swatch_rect = pygame.Rect(cx, cy, c_swatch_size, c_swatch_size)

            is_chosen_by_other = any(player_color_indices[p_other] == c_idx for p_other in range(num_players) if p_other != i)
            is_selected_by_me = (player_color_indices[i] == c_idx)

            if is_chosen_by_other:
                pygame.draw.rect(screen, (20, 25, 35), swatch_rect, border_radius=6)
                pygame.draw.rect(screen, (40, 45, 60), swatch_rect, width=1, border_radius=6)
                pygame.draw.line(screen, (80, 90, 110), (cx+3, cy+3), (cx+c_swatch_size-3, cy+c_swatch_size-3), 2)
            else:
                pygame.draw.rect(screen, c_obj["rgb"], swatch_rect, border_radius=6)
                if is_selected_by_me:
                    pygame.draw.rect(screen, (255, 255, 255), swatch_rect, width=3, border_radius=6)

    # Start Match Button
    play_btn = pygame.Rect(card.centerx - int(card_w * 0.22), card.bottom - int(card_h * 0.10), int(card_w * 0.44), int(card_h * 0.080))
    pygame.draw.rect(screen, (255, 51, 102), play_btn, border_radius=10)
    pt = get_scaled_font(play_btn.height * 0.48, bold=True).render("START MATCH", True, (255, 255, 255))
    screen.blit(pt, (play_btn.centerx - pt.get_width()//2, play_btn.centery - pt.get_height()//2))

def draw_playing(w, h, time_left):
    draw_animated_background(w, h)
    theme = THEMES[selected_theme_key]
    ox, oy, cs, card_x, card_y, card_size = board.get_layout_geometry(w, h)

    # Top Bar
    bar_h = max(42, int(h * 0.078))
    top_bar = pygame.Rect(int(w * 0.03), int(h * 0.015), w - int(w * 0.06), bar_h)
    pygame.draw.rect(screen, theme["panel"], top_bar, border_radius=12)
    pygame.draw.rect(screen, theme["panel_border"], top_bar, width=1, border_radius=12)

    # Menu Button
    m_btn = pygame.Rect(top_bar.left + 10, top_bar.centery - int(bar_h * 0.35), int(top_bar.width * 0.09), int(bar_h * 0.70))
    pygame.draw.rect(screen, theme["panel_surface"], m_btn, border_radius=8)
    pygame.draw.rect(screen, theme["panel_border"], m_btn, width=1, border_radius=8)
    mt = get_scaled_font(m_btn.height * 0.42, bold=True).render("⮌ Menu", True, theme["text_main"])
    screen.blit(mt, (m_btn.centerx - mt.get_width()//2, m_btn.centery - mt.get_height()//2))

    # Pause Button
    p_btn = pygame.Rect(m_btn.right + 8, top_bar.centery - int(bar_h * 0.35), int(top_bar.width * 0.09), int(bar_h * 0.70))
    pygame.draw.rect(screen, (255, 195, 0), p_btn, border_radius=8)
    pst = get_scaled_font(p_btn.height * 0.42, bold=True).render("⏸ Pause", True, (0, 0, 0))
    screen.blit(pst, (p_btn.centerx - pst.get_width()//2, p_btn.centery - pst.get_height()//2))

    # Restart Button
    r_btn = pygame.Rect(top_bar.right - int(top_bar.width * 0.10) - 10, top_bar.centery - int(bar_h * 0.35), int(top_bar.width * 0.10), int(bar_h * 0.70))
    pygame.draw.rect(screen, (255, 51, 102), r_btn, border_radius=8)
    rt = get_scaled_font(r_btn.height * 0.42, bold=True).render("🔄 Restart", True, (255, 255, 255))
    screen.blit(rt, (r_btn.centerx - rt.get_width()//2, r_btn.centery - rt.get_height()//2))

    # Dynamic Center Status & Large Timer Centerpiece
    is_panic = (time_left <= 6.0)
    panic_scale = 1.0 + (0.15 * math.sin(global_tick * 0.38)) if is_panic else 1.0

    center_badge_w = min(int(top_bar.width * (0.52 if is_panic else 0.48)), 500)
    center_badge_h = int(bar_h * 0.86)
    center_badge = pygame.Rect(top_bar.centerx - center_badge_w//2, top_bar.centery - center_badge_h//2, center_badge_w, center_badge_h)

    curr_turn_rgb = get_player_rgb(board.current_turn)
    curr_p_name = player_names[board.current_turn]
    timer_col = (255, 40, 80) if is_panic else (16, 255, 130)

    pygame.draw.rect(screen, (10, 14, 24), center_badge, border_radius=10)
    pygame.draw.rect(screen, timer_col if is_panic else curr_turn_rgb, center_badge, width=2 if is_panic else 1, border_radius=10)

    pygame.draw.circle(screen, curr_turn_rgb, (center_badge.left + 16, center_badge.centery), 6)
    name_txt = get_scaled_font(center_badge_h * 0.44, bold=True).render(f"{curr_p_name}'s Turn", True, curr_turn_rgb)
    screen.blit(name_txt, (center_badge.left + 28, center_badge.centery - name_txt.get_height()//2))

    t_sec_val = int(math.ceil(time_left))
    timer_badge_w = int(center_badge_w * (0.36 if is_panic else 0.30))
    timer_badge_rect = pygame.Rect(center_badge.right - timer_badge_w - 6, center_badge.top + 3, timer_badge_w, center_badge_h - 6)

    pygame.draw.rect(screen, (34, 10, 18) if is_panic else theme["panel_surface"], timer_badge_rect, border_radius=6)
    pygame.draw.rect(screen, timer_col, timer_badge_rect, width=2 if is_panic else 1, border_radius=6)

    timer_str = f"⏱ {t_sec_val}s"
    t_font_size = timer_badge_rect.height * (0.72 * panic_scale if is_panic else 0.58)
    t_surf = get_scaled_font(t_font_size, bold=True).render(timer_str, True, timer_col)
    screen.blit(t_surf, (timer_badge_rect.centerx - t_surf.get_width()//2, timer_badge_rect.centery - t_surf.get_height()//2))

    # Solid Board Card Surface
    board_card = pygame.Rect(card_x, card_y, card_size, card_size)
    card_shadow = board_card.copy()
    card_shadow.y += 4
    pygame.draw.rect(screen, (5, 8, 15), card_shadow, border_radius=16)
    pygame.draw.rect(screen, theme["panel_surface"], board_card, border_radius=16)
    pygame.draw.rect(screen, theme["panel_border"], board_card, width=2, border_radius=16)

    # Board Render Fills
    board_surf = pygame.Surface((w, h), pygame.SRCALPHA)
    for r in range(grid_size):
        for c in range(grid_size):
            owner = board.boxes[r][c]
            if owner is not None:
                bx = ox + c * cs
                by = oy + r * cs
                owner_rgb = get_player_rgb(owner)
                pygame.draw.rect(board_surf, (owner_rgb[0], owner_rgb[1], owner_rgb[2], 85), (bx, by, cs, cs))
                pygame.draw.rect(board_surf, (owner_rgb[0], owner_rgb[1], owner_rgb[2], 160), (bx+1, by+1, cs-2, cs-2), width=1)
                
                initial = player_names[owner][:1].upper() if player_names[owner] else "P"
                in_font = get_scaled_font(cs * 0.48, bold=True)
                let_s = in_font.render(initial, True, owner_rgb)
                screen.blit(let_s, (bx + cs//2 - let_s.get_width()//2, by + cs//2 - let_s.get_height()//2))
    screen.blit(board_surf, (0, 0))

    # Grid Guides
    for r in range(board.dot_count):
        for c in range(grid_size):
            x1, y1 = ox + c * cs, oy + r * cs
            x2 = x1 + cs
            if board.h_lines[r][c] is None:
                pygame.draw.line(screen, theme["grid_idle"], (x1, y1), (x2, y1), max(2, cs//28))

    for r in range(grid_size):
        for c in range(board.dot_count):
            x1, y1 = ox + c * cs, oy + r * cs
            y2 = y1 + cs
            if board.v_lines[r][c] is None:
                pygame.draw.line(screen, theme["grid_idle"], (x1, y1), (x1, y2), max(2, cs//28))

    # Placed Lines
    line_thickness = max(3, int(cs * 0.09))
    for r in range(board.dot_count):
        for c in range(grid_size):
            owner = board.h_lines[r][c]
            if owner is not None:
                col = get_player_rgb(owner)
                pygame.draw.line(screen, col, (ox + c*cs, oy + r*cs), (ox + (c+1)*cs, oy + r*cs), line_thickness)

    for r in range(grid_size):
        for c in range(board.dot_count):
            owner = board.v_lines[r][c]
            if owner is not None:
                col = get_player_rgb(owner)
                pygame.draw.line(screen, col, (ox + c*cs, oy + r*cs), (ox + c*cs, oy + (r+1)*cs), line_thickness)

    # Advanced Vector Line Placement Animation
    now = time.time()
    ANIM_DURATION = 0.16
    active_anims = []
    glow_overlay = pygame.Surface((w, h), pygame.SRCALPHA)

    for anim in board.animating_lines:
        progress = min(1.0, (now - anim["start_t"]) / ANIM_DURATION)
        col = get_player_rgb(anim["p"])
        extra_th = max(5, int(line_thickness * 1.65))

        if anim["type"] == "H":
            if anim.get("dir", 1) == 1:
                x1 = ox + anim["c"] * cs
                x2 = x1 + int(cs * progress)
            else:
                x1 = ox + (anim["c"] + 1) * cs
                x2 = x1 - int(cs * progress)
            y = oy + anim["r"] * cs
            
            pygame.draw.line(screen, col, (x1, y), (x2, y), extra_th)
            pygame.draw.line(screen, (255, 255, 255), (x1, y), (x2, y), max(2, extra_th // 3))
            pygame.draw.circle(glow_overlay, (col[0], col[1], col[2], 180), (x2, y), max(8, int(cs * 0.18)))
            pygame.draw.circle(screen, (255, 255, 255), (x2, y), max(4, extra_th // 2))

            if progress >= 1.0:
                burst_rad = int(cs * 0.24)
                pygame.draw.circle(glow_overlay, (col[0], col[1], col[2], 120), ((x1 + x2)//2, y), burst_rad)
        else:
            if anim.get("dir", 1) == 1:
                y1 = oy + anim["r"] * cs
                y2 = y1 + int(cs * progress)
            else:
                y1 = oy + (anim["r"] + 1) * cs
                y2 = y1 - int(cs * progress)
            x = ox + anim["c"] * cs

            pygame.draw.line(screen, col, (x, y1), (x, y2), extra_th)
            pygame.draw.line(screen, (255, 255, 255), (x, y1), (x, y2), max(2, extra_th // 3))
            pygame.draw.circle(glow_overlay, (col[0], col[1], col[2], 180), (x, y2), max(8, int(cs * 0.18)))
            pygame.draw.circle(screen, (255, 255, 255), (x, y2), max(4, extra_th // 2))

            if progress >= 1.0:
                burst_rad = int(cs * 0.24)
                pygame.draw.circle(glow_overlay, (col[0], col[1], col[2], 120), (x, (y1 + y2)//2), burst_rad)

        if progress < 1.0:
            active_anims.append(anim)
    board.animating_lines = active_anims
    screen.blit(glow_overlay, (0, 0))

    # Target Guidance Pulses
    dot_r = max(3, int(cs * 0.08))
    if drag_start_dot is not None:
        valid_neighbors = board.get_valid_neighbors(drag_start_dot)
        pulse_phase = (global_tick % 30) / 30.0
        ring_rad = dot_r + int(pulse_phase * (cs * 0.22))
        ring_alpha = int((1.0 - pulse_phase) * 230)
        curr_turn_col = get_player_rgb(board.current_turn)

        aura_surf = pygame.Surface((w, h), pygame.SRCALPHA)
        for nr, nc in valid_neighbors:
            nx, ny = board.get_dot_coords(nr, nc, w, h)
            pygame.draw.circle(aura_surf, (curr_turn_col[0], curr_turn_col[1], curr_turn_col[2], ring_alpha), (nx, ny), ring_rad, width=2)
            pygame.draw.circle(aura_surf, (curr_turn_col[0], curr_turn_col[1], curr_turn_col[2], 140), (nx, ny), dot_r + 3)
        screen.blit(aura_surf, (0, 0))

    # Drag Line
    if drag_start_dot is not None:
        d_r, d_c = drag_start_dot
        sx, sy = board.get_dot_coords(d_r, d_c, w, h)
        mx, my = pygame.mouse.get_pos()
        curr_col = get_player_rgb(board.current_turn)
        pygame.draw.line(screen, curr_col, (sx, sy), (mx, my), line_thickness)
        pygame.draw.circle(screen, curr_col, (sx, sy), max(4, cs//9))

    # Dots
    for r in range(board.dot_count):
        for c in range(board.dot_count):
            px, py = ox + c * cs, oy + r * cs
            pygame.draw.circle(screen, (8, 12, 20), (px, py), dot_r + 2)
            pygame.draw.circle(screen, theme["dot"], (px, py), dot_r)

    if drag_start_dot is not None:
        dsx, dsy = board.get_dot_coords(drag_start_dot[0], drag_start_dot[1], w, h)
        pygame.draw.circle(screen, (255, 255, 255), (dsx, dsy), dot_r + 3, width=2)

    # Bottom Scoreboard
    sb_w = w - int(w * 0.06)
    sb_h = max(56, int(h * 0.12))
    sb_rect = pygame.Rect(int(w * 0.03), h - sb_h - max(8, int(h * 0.015)), sb_w, sb_h)
    pygame.draw.rect(screen, theme["panel"], sb_rect, border_radius=12)
    pygame.draw.rect(screen, theme["panel_border"], sb_rect, width=1, border_radius=12)

    card_spacing = 8
    card_w = (sb_w - 16 - ((num_players - 1) * card_spacing)) // num_players
    for i in range(num_players):
        cx = sb_rect.left + 8 + (i * (card_w + card_spacing))
        card_r = pygame.Rect(cx, sb_rect.top + 6, card_w, sb_h - 12)
        is_turn = (i == board.current_turn)
        p_col = get_player_rgb(i)

        pygame.draw.rect(screen, theme["panel_surface"], card_r, border_radius=8)
        pygame.draw.rect(screen, p_col if is_turn else theme["panel_border"], card_r, width=2 if is_turn else 1, border_radius=8)

        av_r = max(8, int(card_r.height * 0.28))
        pygame.draw.circle(screen, p_col, (card_r.left + av_r + 6, card_r.centery), av_r)
        
        av_txt = get_scaled_font(av_r * 1.1, bold=True).render(player_names[i][:1].upper(), True, (255, 255, 255))
        screen.blit(av_txt, (card_r.left + av_r + 6 - av_txt.get_width()//2, card_r.centery - av_txt.get_height()//2))

        nm = get_scaled_font(card_r.height * 0.26, bold=True).render(player_names[i], True, theme["text_main"])
        screen.blit(nm, (card_r.left + (av_r * 2) + 12, card_r.top + int(card_r.height * 0.16)))

        sc_lbl = get_scaled_font(card_r.height * 0.20).render("Boxes:", True, theme["text_sub"])
        screen.blit(sc_lbl, (card_r.left + (av_r * 2) + 12, card_r.top + int(card_r.height * 0.52)))

        sc_num = get_scaled_font(card_r.height * 0.40, bold=True).render(str(board.scores[i]), True, p_col)
        screen.blit(sc_num, (card_r.right - sc_num.get_width() - 8, card_r.centery - sc_num.get_height()//2))

def draw_gameover_dialog(w, h):
    theme = THEMES[selected_theme_key]
    overlay = pygame.Surface((w, h), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 215))
    screen.blit(overlay, (0, 0))

    modal_w, modal_h = min(int(w * 0.8), 500), min(int(h * 0.78), 460)
    rect = pygame.Rect((w - modal_w)//2, (h - modal_h)//2, modal_w, modal_h)

    pygame.draw.rect(screen, theme["panel"], rect, border_radius=18)
    pygame.draw.rect(screen, theme["panel_border"], rect, width=2, border_radius=18)

    ranked = sorted([(i, board.scores[i]) for i in range(num_players)], key=lambda x: x[1], reverse=True)
    is_tie = (ranked[0][1] == ranked[1][1])
    winner_idx = ranked[0][0]

    w_title = "MATCH TIED!" if is_tie else f"{player_names[winner_idx]} WINS!"
    w_col = theme["text_main"] if is_tie else get_player_rgb(winner_idx)

    wt = get_scaled_font(modal_h * 0.08, bold=True).render(w_title, True, w_col)
    screen.blit(wt, (rect.centerx - wt.get_width()//2, rect.top + int(modal_h * 0.06)))

    for rank, (p_idx, sc) in enumerate(ranked):
        r_y = rect.top + int(modal_h * 0.18) + (rank * int(modal_h * 0.10))
        r_rect = pygame.Rect(rect.left + 25, r_y, modal_w - 50, int(modal_h * 0.085))
        p_col = get_player_rgb(p_idx)
        
        pygame.draw.rect(screen, theme["panel_surface"], r_rect, border_radius=8)
        p_name = get_scaled_font(r_rect.height * 0.45, bold=True).render(f"#{rank+1}  {player_names[p_idx]}", True, p_col)
        p_sc = get_scaled_font(r_rect.height * 0.45, bold=True).render(f"{sc} Boxes", True, theme["text_main"])
        screen.blit(p_name, (r_rect.left + 15, r_rect.centery - p_name.get_height()//2))
        screen.blit(p_sc, (r_rect.right - 15 - p_sc.get_width(), r_rect.centery - p_sc.get_height()//2))

    rematch_btn = pygame.Rect(rect.left + 25, rect.bottom - int(modal_h * 0.16), (modal_w - 60)//2, int(modal_h * 0.10))
    pygame.draw.rect(screen, (0, 210, 255), rematch_btn, border_radius=8)
    rt = get_scaled_font(rematch_btn.height * 0.45, bold=True).render("Rematch", True, (0, 0, 0))
    screen.blit(rt, (rematch_btn.centerx - rt.get_width()//2, rematch_btn.centery - rt.get_height()//2))

    menu_btn = pygame.Rect(rect.right - 25 - rematch_btn.width, rect.bottom - int(modal_h * 0.16), rematch_btn.width, rematch_btn.height)
    pygame.draw.rect(screen, theme["panel_border"], menu_btn, border_radius=8)
    mt = get_scaled_font(menu_btn.height * 0.45, bold=True).render("Main Menu", True, theme["text_main"])
    screen.blit(mt, (menu_btn.centerx - mt.get_width()//2, menu_btn.centery - mt.get_height()//2))

# ================= MASTER LOOP =================
last_timer_update = time.time()

while True:
    global_tick += 1
    current_time = time.time()
    dt = current_time - last_timer_update
    last_timer_update = current_time

    cur_w, cur_h = screen.get_size()
    mx, my = pygame.mouse.get_pos()

    # Active Turn Timer Logic
    if current_state == "PLAYING" and not is_paused and confirm_modal is None and not show_about:
        time_remaining -= dt
        if time_remaining <= 0.0:
            board.auto_play_random_move()
            time_remaining = TURN_DURATION
            if board.is_game_over():
                current_state = "GAMEOVER"

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        elif event.type == pygame.VIDEORESIZE:
            bg_cache = None

        # Focus Auto-Pause (Alt+Tab / App Switch)
        elif event.type == pygame.ACTIVEEVENT:
            if hasattr(event, 'gain') and event.gain == 0:
                if current_state == "PLAYING":
                    is_paused = True

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_F11:
                toggle_true_borderless_fullscreen()
            elif event.key in (pygame.K_p, pygame.K_SPACE) and current_state == "PLAYING" and confirm_modal is None and not show_about:
                is_paused = not is_paused

        # About Modal
        if show_about:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                modal_w, modal_h = min(int(cur_w * 0.75), 560), min(int(cur_h * 0.70), 390)
                rect = pygame.Rect((cur_w - modal_w)//2, (cur_h - modal_h)//2, modal_w, modal_h)
                btn = pygame.Rect(rect.centerx - 70, rect.bottom - int(modal_h * 0.14), 140, int(modal_h * 0.09))
                if btn.collidepoint(mx, my) or not rect.collidepoint(mx, my):
                    show_about = False
            continue

        # Pause Modal
        if is_paused and current_state == "PLAYING":
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                modal_w, modal_h = min(int(cur_w * 0.75), 440), min(int(cur_h * 0.42), 210)
                rect = pygame.Rect((cur_w - modal_w)//2, (cur_h - modal_h)//2, modal_w, modal_h)
                btn_w, btn_h = int(modal_w * 0.52), int(modal_h * 0.24)
                resume_btn = pygame.Rect(rect.centerx - btn_w // 2, rect.bottom - btn_h - 22, btn_w, btn_h)
                if resume_btn.collidepoint(mx, my) or not rect.collidepoint(mx, my):
                    is_paused = False
                    last_timer_update = time.time()
            continue

        # Confirmation Modal
        if confirm_modal is not None:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                modal_w, modal_h = min(int(cur_w * 0.75), 450), min(int(cur_h * 0.48), 230)
                rect = pygame.Rect((cur_w - modal_w)//2, (cur_h - modal_h)//2, modal_w, modal_h)
                btn_w, btn_h = int(modal_w * 0.38), int(modal_h * 0.18)
                yes_btn = pygame.Rect(rect.left + 30, rect.bottom - btn_h - 18, btn_w, btn_h)
                no_btn = pygame.Rect(rect.right - 30 - btn_w, rect.bottom - btn_h - 18, btn_w, btn_h)

                if yes_btn.collidepoint(mx, my):
                    if confirm_modal == 'QUIT':
                        pygame.quit()
                        sys.exit()
                    elif confirm_modal == 'RESTART':
                        board = GameBoard(grid_size, num_players, player_color_indices)
                        time_remaining = TURN_DURATION
                        last_timer_update = time.time()
                    elif confirm_modal == 'MENU':
                        current_state = "MENU"
                    confirm_modal = None
                    is_paused = False
                elif no_btn.collidepoint(mx, my):
                    confirm_modal = None
                    last_timer_update = time.time()
            continue

        if current_state == "WELCOME":
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                hero_w = min(int(cur_w * 0.72), 650)
                hero_h = min(int(cur_h * 0.72), 460)
                hero_rect = pygame.Rect((cur_w - hero_w) // 2, (cur_h - hero_h) // 2 - 10, hero_w, hero_h)
                btn_w = int(hero_w * 0.50)
                btn_h = int(hero_h * 0.13)

                play_btn = pygame.Rect(hero_rect.centerx - btn_w // 2, hero_rect.top + int(hero_h * 0.54), btn_w, btn_h)
                
                btn_row_y = hero_rect.top + int(hero_h * 0.73)
                abt_w = int(btn_w * 0.46)
                abt_btn = pygame.Rect(hero_rect.centerx - abt_w - 8, btn_row_y, abt_w, int(btn_h * 0.75))
                exit_btn = pygame.Rect(hero_rect.centerx + 8, btn_row_y, abt_w, int(btn_h * 0.75))

                if play_btn.collidepoint(mx, my):
                    current_state = "MENU"
                elif abt_btn.collidepoint(mx, my):
                    about_type_timer = 0
                    show_about = True
                elif exit_btn.collidepoint(mx, my):
                    confirm_modal = 'QUIT'

        elif current_state == "MENU":
            card_w = min(int(cur_w * 0.94), 980)
            card_h = min(int(cur_h * 0.82), 620)
            card = pygame.Rect((cur_w - card_w)//2, int(cur_h * 0.12), card_w, card_h)

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                abt_w, abt_h = max(70, int(cur_w * 0.075)), max(28, int(cur_h * 0.042))
                abt_btn = pygame.Rect(cur_w - (abt_w * 2) - int(cur_w * 0.04) - 8, int(cur_h * 0.024), abt_w, abt_h)
                exit_btn = pygame.Rect(cur_w - abt_w - int(cur_w * 0.03), int(cur_h * 0.024), abt_w, abt_h)

                if abt_btn.collidepoint(mx, my):
                    about_type_timer = 0
                    show_about = True
                elif exit_btn.collidepoint(mx, my):
                    confirm_modal = 'QUIT'

                t_y = card.top + int(card_h * 0.030)
                t_keys = list(THEMES.keys())
                btn_w = (card_w - 60 - ((len(t_keys)-1)*10)) // len(t_keys)
                for i, tname in enumerate(t_keys):
                    b = pygame.Rect(card.left + 30 + (i*(btn_w+10)), t_y + int(card_h * 0.040), btn_w, int(card_h * 0.058))
                    if b.collidepoint(mx, my):
                        selected_theme_key = tname

                p_y = card.top + int(card_h * 0.155)
                for i, cnt in enumerate([2, 3, 4, 5]):
                    b = pygame.Rect(card.left + 30 + (i * 76), p_y + int(card_h * 0.040), 70, int(card_h * 0.058))
                    if b.collidepoint(mx, my):
                        num_players = cnt

                for i, sz in enumerate(available_grids):
                    b = pygame.Rect(card.left + 360 + (i * 68), p_y + int(card_h * 0.040), 62, int(card_h * 0.058))
                    if b.collidepoint(mx, my):
                        grid_size = sz

                n_y = card.top + int(card_h * 0.285)
                row_h = int(card_h * 0.085)
                active_input_idx = None
                select_all = False

                for i in range(num_players):
                    row_y = n_y + int(card_h * 0.038) + (i * (row_h + 5))
                    row_rect = pygame.Rect(card.left + 30, row_y, card_w - 60, row_h)
                    in_box = pygame.Rect(row_rect.left + 12, row_rect.top + 5, int(row_rect.width * 0.34), row_rect.height - 10)
                    
                    if in_box.collidepoint(mx, my):
                        active_input_idx = i

                    col_start_x = in_box.right + 25
                    c_swatch_size = int(row_rect.height * 0.55)
                    for c_idx, c_obj in enumerate(AVAILABLE_COLORS):
                        cx = col_start_x + (c_idx * (c_swatch_size + 8))
                        cy = row_rect.centery - c_swatch_size // 2
                        swatch_rect = pygame.Rect(cx, cy, c_swatch_size, c_swatch_size)

                        if swatch_rect.collidepoint(mx, my):
                            is_chosen_by_other = any(player_color_indices[p_other] == c_idx for p_other in range(num_players) if p_other != i)
                            if not is_chosen_by_other:
                                player_color_indices[i] = c_idx

                play_btn = pygame.Rect(card.centerx - int(card_w * 0.22), card.bottom - int(card_h * 0.10), int(card_w * 0.44), int(card_h * 0.080))
                if play_btn.collidepoint(mx, my):
                    board = GameBoard(grid_size, num_players, player_color_indices)
                    time_remaining = TURN_DURATION
                    last_timer_update = time.time()
                    is_paused = False
                    current_state = "PLAYING"

            elif event.type == pygame.KEYDOWN and active_input_idx is not None:
                if event.key == pygame.K_a and (pygame.key.get_mods() & pygame.KMOD_CTRL):
                    select_all = True
                elif event.key == pygame.K_BACKSPACE:
                    if select_all:
                        player_names[active_input_idx] = ""
                        select_all = False
                    else:
                        player_names[active_input_idx] = player_names[active_input_idx][:-1]
                elif event.key == pygame.K_RETURN:
                    active_input_idx = None
                    select_all = False
                else:
                    if select_all:
                        player_names[active_input_idx] = ""
                        select_all = False
                    if len(player_names[active_input_idx]) < 12 and event.unicode.isprintable():
                        player_names[active_input_idx] += event.unicode

        elif current_state == "PLAYING":
            bar_h = max(42, int(cur_h * 0.078))
            top_bar = pygame.Rect(int(cur_w * 0.03), int(cur_h * 0.015), cur_w - int(cur_w * 0.06), bar_h)
            m_btn = pygame.Rect(top_bar.left + 10, top_bar.centery - int(bar_h * 0.35), int(top_bar.width * 0.09), int(bar_h * 0.70))
            p_btn = pygame.Rect(m_btn.right + 8, top_bar.centery - int(bar_h * 0.35), int(top_bar.width * 0.09), int(bar_h * 0.70))
            r_btn = pygame.Rect(top_bar.right - int(top_bar.width * 0.10) - 10, top_bar.centery - int(bar_h * 0.35), int(top_bar.width * 0.10), int(bar_h * 0.70))

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if m_btn.collidepoint(mx, my):
                    confirm_modal = 'MENU'
                elif p_btn.collidepoint(mx, my):
                    is_paused = True
                elif r_btn.collidepoint(mx, my):
                    confirm_modal = 'RESTART'
                else:
                    clicked_dot = board.get_dot_at_pos(mx, my, cur_w, cur_h)
                    if clicked_dot:
                        drag_start_dot = clicked_dot

            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                if drag_start_dot is not None:
                    target_dot = board.get_dot_at_pos(mx, my, cur_w, cur_h)
                    if target_dot and target_dot != drag_start_dot:
                        if board.connect_dots(drag_start_dot, target_dot):
                            time_remaining = TURN_DURATION
                            last_timer_update = time.time()
                            if board.is_game_over():
                                current_state = "GAMEOVER"
                    drag_start_dot = None

        elif current_state == "GAMEOVER":
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                modal_w, modal_h = min(int(cur_w * 0.8), 500), min(int(cur_h * 0.78), 460)
                rect = pygame.Rect((cur_w - modal_w)//2, (cur_h - modal_h)//2, modal_w, modal_h)
                rematch_btn = pygame.Rect(rect.left + 25, rect.bottom - int(modal_h * 0.16), (modal_w - 60)//2, int(modal_h * 0.10))
                menu_btn = pygame.Rect(rect.right - 25 - rematch_btn.width, rect.bottom - int(modal_h * 0.16), rematch_btn.width, rematch_btn.height)

                if rematch_btn.collidepoint(mx, my):
                    board = GameBoard(grid_size, num_players, player_color_indices)
                    time_remaining = TURN_DURATION
                    last_timer_update = time.time()
                    current_state = "PLAYING"
                elif menu_btn.collidepoint(mx, my):
                    current_state = "MENU"

    # Screen Graphics Routing
    if current_state == "WELCOME":
        draw_welcome_screen(cur_w, cur_h)
    elif current_state == "MENU":
        draw_menu(cur_w, cur_h)
    elif current_state == "PLAYING":
        draw_playing(cur_w, cur_h, max(0.0, time_remaining))
    elif current_state == "GAMEOVER":
        draw_playing(cur_w, cur_h, 0.0)
        draw_gameover_dialog(cur_w, cur_h)

    if show_about:
        draw_about_dialog(cur_w, cur_h)
    elif is_paused and current_state == "PLAYING":
        draw_pause_dialog(cur_w, cur_h)
    elif confirm_modal is not None:
        draw_confirmation_dialog(cur_w, cur_h)

    pygame.display.flip()
    clock.tick(60)