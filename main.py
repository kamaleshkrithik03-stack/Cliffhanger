import os
import pygame
import math
import random #these imports are in the back of my hand rn im so use to it
import sys

pygame.init()
WIDTH = 1000 # for now  i might chage to make it full screen
HEIGHT = 800 #not gonna do a config.py too lazy
screen = pygame.display.set_mode(WIDTH, HEIGHT)
pygame.display.set_caption("Cliffhanger is the name i could come up with")
clock = pygame.time.Clock()
FONT_BIG = pygame.font.SysFont("arial", 42, bold=True) #im sticking to arial(maybe times new roman) as im not experimenting with orbitron and all that shi
FONT_MED = pygame.font.SysFont("arial", 25, bold=True) #maybe idk ill see
FONT_SMALL = pygame.font.SysFont("arial", 18) #not bold

LEVELS = [
    {"level": 1, "time": 10, "gravity": 500, "max_safe_vy": 420}, # ok so basically what ive done here is my idea is that the char/sprite will be floating in air in a cliff and as levels goes up u can see the time(most hardest) decreases
    {"level": 2, "time": 8, "gravity": 650, "max_safe_vy": 380}, # copy pasted from last line 
    {"level": 3, "time": 5, "gravity": 750, "max_safe_vy": 340},
]
GROUND_Y = HEIGHT - 60
DROP_START_X = 340 #ugghh ofc i have to use pycase not snakecase its of i have to have caps lock on evry timr
DROP_START_Y = 150

def load_transparent_asset(filename, size, fallback_color):
    if os.path.exists(filename):
        img = pygame.image.load(filename).convert_alpha()
        return pygame.transform.smoothscale(img, size)
    surf = pygame.Surface(size, pygame.SRCALPHA)
    pygame.draw.rect(surf, fallback_color, (0, 0, size[0], size[1],), border_radius=12)
    return surf
cliff_img = load_transparent_asset("cliff.png", (320, 560), (95, 85, 80, 255))
player_img = load_transparent_asset("sprite.png", (64, 64), (255, 210, 80, 255))
def compute_contraption_stats(strokes):
    all_points = [pt for stroke in strokes for pt in stroke]
    if len(all_points) < 2:
        return 0.0, 0.0, 1.0
    xs = [p[0] for p in all_points]
    ys = [p[1] for p in all_points]
    span_x = max(xs) - min(xs)
    span_y = max(ys) - min(ys)
    total_length = 0.0
    for stroke in strokes:
        for i in range(1, len(stroke)):
            dx = stroke[i][0] - stroke[i - 1][0]
            dy = stroke[i][1] - stroke[i - 1][1]
            total_length += math.hypot(dx, dy)#as usual we see pythagoras

    drag_factor = min(0.0045, (span_x * 0.000018))
    cushion_bonus = min(220.0, total_length * 0.18 + (span_y * 0.25))
    mass_factor = 1.0 + min(0.35, total_length * 0.00015)
    return drag_factor, cushion_bonus, mass_factor
class Game:
    def __init__(self):
        self.level_idx = 0
        self.reset_level()
    def reset_level(self):
        cfg = LEVELS[self.level_idx]
        self.state = "DRAW"
        self.time_left = cfg["time"]
        self.player_x = float(DROP_START_X)
        self.player_y = float(DROP_START_Y)
        self.vy = 0.0
        self.strokes = []
        self.current_stroke = []
        self.is_drawing = False
        self.survived = False
        self.impact_speed = 0
        self.safe_limit = cfg["max_safe_vy"]
    def start_drop(self):
        self.state = "DROP"
        self.is_drawing = False
        if self.current_stroke:
            self.strokes.append(self.current_stroke)
            self.current_stroke = []
        self.drag, cushion, self.mass = compute_contraption_stats(self.strokes)
        self.safe_limit = LEVELS[self.level_idx]["max_safe_vy"] + cushion
game = Game()
running = True
while running:
    dt = clock.tick(60) / 1000
    cfg = LEVELS[game.level_idx]
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE and game.state == "DRAW":
                game.start_drop()
            elif event.key == pygame.K_c and game.state == "DRAW":
                game.strokes.clear()
                game.current_stroke.clear()
            elif event.key == pygame.K_r:
                game.reset_level()
            elif event.key == pygame.K_RETURN and game.state == "RESULT":
                if game.survived:
                    game.level_idx = (game.level_idx + 1) % len(LEVELS)
                game.reset_level()
        elif game.state == "DRAW":
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1: #finally on to the MOUSE stuff always my fav
                game.is_drawing = True
                rel_pt = (event.pos[0] - game.player_x, event.pos[1] - game.player_y)
                game.current_stroke = [rel_pt]
            elif event.type == pygame.MOUSEMOTION and game.is_drawing:
                rel_pt = (event.pos[0] - game.player_x, event.pos[1] - game.player_y)
                if math.hypot(rel_pt[0], rel_pt[1]) <= 160:
                    game.current_stroke.append(rel_pt)
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 2 and game.is_drawing:
                game.is_drawing = False
                if len(game.current_stroke) > 1:
                    game.strokes.append(game.current_stroke)
                game.current_stroke = []
    if game.state == "DRAW":
        game.time_left -= dt
        if game.time_left <= 0:
            game.time_left = 0
            game.start_drop()
    elif game.state == "DROP":
        accel = (cfg["gravity"] * game.mass) - (game.drag * (game.vy ** 2))
        game.vy += accel * dt
        game.player_y += game.vy * dt
        if game.player_y + 32 >= GROUND_Y:
            game.player_y = GROUND_Y - 32
            game.impact_speed = game.vy
            game.survived = game.impact_speed <= game.safe_limit
            game.state = "RESULT"
    screen.fill((135, 200, 235)) #the best colour choice ig
    pygame.draw.rect(screen, (65, 150, 75), (0, GROUND_Y, WIDTH, HEIGHT - GROUND_Y))
    screen.blit(cliff_img, (0, GROUND_Y - cliff_img.get_height()))
    if game.state == "DRAW":
        pygame.draw.circle(
            screen, (255, 255, 255), (int(game.player_x), int(game.player_y)), 160, 2
        )
    sprite_rect = player_img.get_rect(center=(int(game.player_x), int(game.player_y)))
    screen.blit(player_img, sprite_rect)
    all_visible_strokes = game.strokes + ([game.current_stroke] if game.current_stroke else [])
    for stroke in all_visible_strokes:
        if len(stroke) > 1:
            world_pts = [(game.player_x + dx, game.player_y + dy) for dx, dy in stroke]
            pygame.draw.lines(screen, (30, 30, 35), False, world_pts, 5)
    lvl_txt = FONT_MED.render(f"level {cfg['level']} / {len(LEVELS)}", True, (20, 20, 20))
    screen.blit(lvl_txt, (20, 15))
    if game.state == "DRAW":
        timer_color = (200, 30, 30) if game.time_left <= 3 else (20, 20, 20)
        timer_txt = FONT_BIG.render(f"go ahead and DRAW! {game.time_left:.1f}s", True, timer_color)
        hint_txt = FONT_SMALL.render("drag mouse inside the ring to build you contraption and[space] for drop", True, (20, 20, 20))
        screen.blit(timer_txt, (WIDTH // 2 - timer_txt.get_width() // 2, 15))
        screen.blit(hint_txt, (WIDTH // 2 - hint_txt.get_width() // 2, 65))
    elif game.state == "DROP":
        spd_txt = FONT_MED.render(f"fall speed: {int(game.vy)} px/s (Safe <= {int(game.safe_limit)})", True, (20, 20, 20))
        screen.blit(spd_txt, (WIDTH // 2 - spd_txt.get_width() // 2, 20))
    elif game.state == "RESULT":
        status = "survived!" if game.survived else "splat! womp womp"
        color = (20, 140, 40) if game.survived else (200, 30, 30)
        res_txt = FONT_BIG.render(status, True, color)
        detail_txt = FONT_MED.render(
            
        )

    

