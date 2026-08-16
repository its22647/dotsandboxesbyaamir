import math

class GameBoard:
    def __init__(self, grid_size, num_players, player_color_indices):
        self.grid_size = grid_size
        self.dot_count = grid_size + 1
        self.num_players = num_players
        self.player_colors = player_color_indices
        
        # Grid line matrices (None = unclaimed, int = player index)
        self.h_lines = [[None for _ in range(grid_size)] for _ in range(self.dot_count)]
        self.v_lines = [[None for _ in range(self.dot_count)] for _ in range(grid_size)]
        self.boxes = [[None for _ in range(grid_size)] for _ in range(grid_size)]
        
        self.scores = [0] * num_players
        self.current_turn = 0
        self.total_boxes = grid_size * grid_size

    def get_layout_geometry(self, screen_w, screen_h):
        top_offset = int(screen_h * 0.10)
        bottom_reserved = int(screen_h * 0.17)
        available_h = screen_h - top_offset - bottom_reserved
        available_w = screen_w - int(screen_w * 0.08)

        board_px = max(260, min(available_w, available_h, int(screen_h * 0.70)))
        cell_size = board_px // self.grid_size
        
        offset_x = (screen_w - (self.grid_size * cell_size)) // 2
        offset_y = top_offset + (available_h - (self.grid_size * cell_size)) // 2
        return offset_x, offset_y, cell_size

    def get_dot_at_pos(self, mx, my, screen_w, screen_h):
        ox, oy, cs = self.get_layout_geometry(screen_w, screen_h)
        tolerance = max(18, cs // 3)
        for r in range(self.dot_count):
            for c in range(self.dot_count):
                dx = ox + c * cs
                dy = oy + r * cs
                if math.hypot(mx - dx, my - dy) <= tolerance:
                    return (r, c)
        return None

    def get_dot_coords(self, r, c, screen_w, screen_h):
        ox, oy, cs = self.get_layout_geometry(screen_w, screen_h)
        return (ox + c * cs, oy + r * cs)

    def connect_dots(self, dot1, dot2):
        r1, c1 = dot1
        r2, c2 = dot2
        dr, dc = abs(r1 - r2), abs(c1 - c2)

        if (dr == 1 and dc == 0) or (dr == 0 and dc == 1):
            if dr == 0:  # Horizontal Line
                row = r1
                col = min(c1, c2)
                if self.h_lines[row][col] is None:
                    self.h_lines[row][col] = self.current_turn
                    self._handle_move()
                    return True
            else:        # Vertical Line
                row = min(r1, r2)
                col = c1
                if self.v_lines[row][col] is None:
                    self.v_lines[row][col] = self.current_turn
                    self._handle_move()
                    return True
        return False

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