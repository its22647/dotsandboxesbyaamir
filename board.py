import math
import time
import random

class GameBoard:
    def __init__(self, grid_size, num_players, player_color_indices, vs_bot=False):
        self.grid_size = grid_size
        self.dot_count = grid_size + 1
        self.num_players = num_players
        self.player_colors = player_color_indices
        self.vs_bot = vs_bot
        
        self.h_lines = [[None for _ in range(grid_size)] for _ in range(self.dot_count)]
        self.v_lines = [[None for _ in range(self.dot_count)] for _ in range(grid_size)]
        self.boxes = [[None for _ in range(grid_size)] for _ in range(grid_size)]
        
        self.animating_lines = []
        
        self.scores = [0] * num_players
        self.current_turn = 0
        self.total_boxes = grid_size * grid_size

    def get_layout_geometry(self, screen_w, screen_h):
        top_bar_h = max(42, int(screen_h * 0.078))
        top_bar_y = max(8, int(screen_h * 0.015))
        top_bar_bottom = top_bar_y + top_bar_h

        sb_h = max(56, int(screen_h * 0.12))
        sb_bottom_margin = max(8, int(screen_h * 0.015))
        sb_top = screen_h - sb_h - sb_bottom_margin

        gap_y = max(12, int(screen_h * 0.022))
        safe_top = top_bar_bottom + gap_y
        safe_bottom = sb_top - gap_y

        available_h = max(140, safe_bottom - safe_top)
        available_w = max(140, screen_w - max(40, int(screen_w * 0.10)))

        card_size = min(available_w, available_h)
        card_x = (screen_w - card_size) // 2
        card_y = safe_top + (available_h - card_size) // 2

        cs = max(14, int(card_size / (self.grid_size + 0.85)))
        padding = (card_size - (self.grid_size * cs)) // 2

        ox = card_x + padding
        oy = card_y + padding

        return ox, oy, cs, card_x, card_y, card_size

    def get_dot_at_pos(self, mx, my, screen_w, screen_h):
        ox, oy, cs, _, _, _ = self.get_layout_geometry(screen_w, screen_h)
        tolerance = max(12, int(cs * 0.38))
        for r in range(self.dot_count):
            for c in range(self.dot_count):
                dx = ox + c * cs
                dy = oy + r * cs
                if math.hypot(mx - dx, my - dy) <= tolerance:
                    return (r, c)
        return None

    def get_dot_coords(self, r, c, screen_w, screen_h):
        ox, oy, cs, _, _, _ = self.get_layout_geometry(screen_w, screen_h)
        return (ox + c * cs, oy + r * cs)

    def get_valid_neighbors(self, dot):
        r, c = dot
        valid = []
        if c + 1 < self.dot_count and self.h_lines[r][c] is None:
            valid.append((r, c + 1))
        if c - 1 >= 0 and self.h_lines[r][c - 1] is None:
            valid.append((r, c - 1))
        if r + 1 < self.dot_count and self.v_lines[r][c] is None:
            valid.append((r + 1, c))
        if r - 1 >= 0 and self.v_lines[r - 1][c] is None:
            valid.append((r - 1, c))
        return valid

    def connect_dots(self, dot1, dot2):
        r1, c1 = dot1
        r2, c2 = dot2
        dr, dc = abs(r1 - r2), abs(c1 - c2)

        if (dr == 1 and dc == 0) or (dr == 0 and dc == 1):
            if dr == 0:
                row = r1
                col = min(c1, c2)
                if self.h_lines[row][col] is None:
                    self.h_lines[row][col] = self.current_turn
                    self.animating_lines.append({
                        "type": "H", "r": row, "c": col,
                        "dir": 1 if c2 > c1 else -1,
                        "start_t": time.time(), "p": self.current_turn
                    })
                    self._handle_move()
                    return True
            else:
                row = min(r1, r2)
                col = c1
                if self.v_lines[row][col] is None:
                    self.v_lines[row][col] = self.current_turn
                    self.animating_lines.append({
                        "type": "V", "r": row, "c": col,
                        "dir": 1 if r2 > r1 else -1,
                        "start_t": time.time(), "p": self.current_turn
                    })
                    self._handle_move()
                    return True
        return False

    def _get_box_sides_count(self, r, c):
        sides = 0
        if self.h_lines[r][c] is not None: sides += 1
        if self.h_lines[r + 1][c] is not None: sides += 1
        if self.v_lines[r][c] is not None: sides += 1
        if self.v_lines[r][c + 1] is not None: sides += 1
        return sides

    def _get_all_available_moves(self):
        moves = []
        for r in range(self.dot_count):
            for c in range(self.grid_size):
                if self.h_lines[r][c] is None:
                    moves.append(('H', r, c))
        for r in range(self.grid_size):
            for c in range(self.dot_count):
                if self.v_lines[r][c] is None:
                    moves.append(('V', r, c))
        return moves

    def _move_creates_box(self, move):
        mtype, r, c = move
        completed = 0
        if mtype == 'H':
            if r > 0 and self._get_box_sides_count(r - 1, c) == 3:
                completed += 1
            if r < self.grid_size and self._get_box_sides_count(r, c) == 3:
                completed += 1
        else:
            if c > 0 and self._get_box_sides_count(r, c - 1) == 3:
                completed += 1
            if c < self.grid_size and self._get_box_sides_count(r, c) == 3:
                completed += 1
        return completed

    def _move_creates_third_side(self, move):
        mtype, r, c = move
        if mtype == 'H':
            if r > 0 and self._get_box_sides_count(r - 1, c) == 2:
                return True
            if r < self.grid_size and self._get_box_sides_count(r, c) == 2:
                return True
        else:
            if c > 0 and self._get_box_sides_count(r, c - 1) == 2:
                return True
            if c < self.grid_size and self._get_box_sides_count(r, c) == 2:
                return True
        return False

    def play_smart_bot_move(self):
        moves = self._get_all_available_moves()
        if not moves:
            return False

        # AI strictly checks if any move can capture boxes without needlessly giving away chains
        winning_moves = [m for m in moves if self._move_creates_box(m) > 0]
        if winning_moves:
            chosen = random.choice(winning_moves)
        else:
            safe_moves = [m for m in moves if not self._move_creates_third_side(m)]
            if safe_moves:
                chosen = random.choice(safe_moves)
            else:
                chosen = random.choice(moves)

        mtype, r, c = chosen
        if mtype == 'H':
            self.h_lines[r][c] = self.current_turn
            self.animating_lines.append({
                "type": "H", "r": r, "c": c, "dir": 1,
                "start_t": time.time(), "p": self.current_turn
            })
        else:
            self.v_lines[r][c] = self.current_turn
            self.animating_lines.append({
                "type": "V", "r": r, "c": c, "dir": 1,
                "start_t": time.time(), "p": self.current_turn
            })

        self._handle_move()
        return True

    def auto_play_random_move(self):
        moves = self._get_all_available_moves()
        if not moves:
            return False

        move_type, r, c = random.choice(moves)
        if move_type == 'H':
            self.h_lines[r][c] = self.current_turn
            self.animating_lines.append({
                "type": "H", "r": r, "c": c, "dir": 1,
                "start_t": time.time(), "p": self.current_turn
            })
        else:
            self.v_lines[r][c] = self.current_turn
            self.animating_lines.append({
                "type": "V", "r": r, "c": c, "dir": 1,
                "start_t": time.time(), "p": self.current_turn
            })

        self._handle_move()
        return True

    def _handle_move(self):
        new_boxes = 0
        for r in range(self.grid_size):
            for c in range(self.grid_size):
                if self.boxes[r][c] is None:
                    top = self.h_lines[r][c]
                    bottom = self.h_lines[r + 1][c]
                    left = self.v_lines[r][c]
                    right = self.v_lines[r][c + 1]
                    if top is not None and bottom is not None and left is not None and right is not None:
                        self.boxes[r][c] = self.current_turn
                        new_boxes += 1
        
        if new_boxes > 0:
            self.scores[self.current_turn] += new_boxes
        else:
            self.current_turn = (self.current_turn + 1) % self.num_players

    def is_game_over(self):
        return sum(self.scores) == self.total_boxes