import os
import pygame
import math
import random #these imports are in the back of my hand rn im so used to it
import sys

pygame.init()
WIDTH = 1000 # for now  i might chage to make it full screen
HEIGHT = 800 #not gonna do a config.py too lazy
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Cliffhanger is the name i could come up with")
clock = pygame.time.Clock()
FONT_BIG = pygame.font.SysFont("comicsansms", 42, bold=True) #im sticking to arial(maybe times new roman) as im not experimenting with orbitron and all that shi
FONT_MED = pygame.font.SysFont("comicsansms", 25, bold=True) #maybe idk ill see alight i change to comicsansms arial seem too formally 
FONT_SMALL = pygame.font.SysFont("comicsansms", 18) #not bold as small

LEVELS = [
    {"level": 1, "time": 8, "gravity": 700, "max_safe_vy": 200, "fluid_rho": 1, "wind_x": 0, "cliff_height": 300, "drop_y": 240}, # ok so basically what ive done here is my idea is that the char/sprite will be floating in air in a cliff and as levels goes up u can see the time(most hardest) decreases
    {"level": 2, "time": 5, "gravity": 800, "max_safe_vy": 180, "fluid_rho": 1.15, "wind_x": 35, "cliff_height": 600, "drop_y": 180}, # copy pasted from last line 
    {"level": 3, "time": 2, "gravity": 900, "max_safe_vy": 140, "fluid_rho": 1.3, "wind_x": -55, "cliff_height": 900, "drop_y": 100}, 
] 
GROUND_Y = HEIGHT - 60
DROP_START_X = 640 #ugghh ofc i have to use pycase not snakecase its of i have to have caps lock on evry timr
DROP_START_Y = 150
DRAW_RADIUS = 160
ANCHOR_RADIUS = 48
def load_transparent_asset(filename, size, fallback_color):
    if os.path.exists(filename):
        img = pygame.image.load(filename).convert_alpha()
        return pygame.transform.smoothscale(img, size)
    surf = pygame.Surface(size, pygame.SRCALPHA)
    pygame.draw.rect(surf, fallback_color, (0, 0, size[0], size[1],), border_radius=12)
    return surf
cliff_img = load_transparent_asset("cliff.png", (320, 560), (95, 85, 80, 255))
player_img = load_transparent_asset("sprite.jpeg", (64, 64), (255, 210, 80, 255))
cloud_base_img = pygame.image.load("cloud.png").convert_alpha() if os.path.exists("cloud.png") else None #i included that os.path exists so that i can make clouds even if there isnt any file (include that in next lines) also i can finally put random to use
def make_random_cloud(scale):
    w = int(150 * scale)
    h = int(64 * scale)
    if cloud_base_img:
        return pygame.transform.smoothscale(cloud_base_img, (w, h))
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    body_h = max(14, int(h * 0.42))
    body_y =  h - body_h - max(4, int(h * 0.08))
    pygame.draw.rect(
        surf,
        (245, 250, 255, 235),
        (int(w * 0.14), body_y, int(w * 0.72), body_h),
        border_radius=max(6, body_h // 2),
    )
    puff_count = random.randint(3, 5)
    for idx in range(puff_count):
        t = (idx + 0.5) / puff_count
        px = int(w * (0.22 + 0.56 * t))
        py = int(body_y - random.randint(2, max(4, int(h * 0.12))))
        rad = random.randint(max(10, int(h * 0.20)), max(14, int(h * 0.3)))
        pygame.draw.circle(surf, (255, 255, 255, 240), (px, py), rad)
    return surf
def spawn_clouds(count=7):
    clouds = []
    for _ in range(count):
        scale = random.uniform(0.6, 1.5) #im juz using random ahh numbers which feel right
        clouds.append({
            "surf": make_random_cloud(scale),
            "x":  float(random.randint(-120, WIDTH + 120)),
            "y": float(random.randint(200, 340)),
            "speed": random.uniform(12, 35) * random.choice([-1, 1]),
        }) 
    return clouds
clouds = spawn_clouds()
def compute_contraption_stats(strokes):
    all_points = [pt for stroke in strokes for pt in stroke]
    if len(all_points) < 2:
        return 0.0, 0.0, 1.0, 0
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

    
    cushion_bonus = min(5, total_length * 0.18 + (span_y * 0.25))
    drag_coeff = min(0.0065, span_x * 0.000024 + total_length * 0.000003) # copy pasted cuz idk this formula but it is drag coeficient
    area_factor = min(3.5, 0.5 + span_x / 90 + total_length / 500)
    mass_factor = 1.0 + min(0.35, total_length * 0.00015)
    return drag_coeff, cushion_bonus, mass_factor, area_factor
class PhysicsNode: #new word node unlocked from godot
    def __init__(self, ox, oy, px, py):
        self.ox = ox
        self.oy = oy
        self.x = px + ox
        self.y = py + oy
        self.vx = 0
        self.vy = 0
class RigPhysics:
    def __init__(self):
        self.nodes = []
        self.links = []
    def build_from_strokes(self, strokes, px, py):
        self.nodes.clear()
        self.links.clear()
        step_spacing = 14
        for stroke in strokes:
            if len(stroke) < 2:
                continue
            sampled = [stroke[0]]
            accum = 0
            for i in range(1, len(stroke)):
                x0, y0 = sampled[-1]
                x1, y1 = stroke[i]
                seg_len = math.hypot(x1 - x0, y1 - y0) #math vibes fr
                if seg_len + accum >= step_spacing:
                    sampled.append((x1, y1))
                    accum = 0
                else:
                    accum += seg_len
            if sampled[-1] != stroke[-1]:
                sampled.append(stroke[-1])
            start_idx = len(self.nodes)
            for ox, oy in sampled:
                self.nodes.append(PhysicsNode(ox, oy, px, py))
            for i in range(start_idx, len(self.nodes) - 1):
                rest = math.hypot(
                    self.nodes[i + 1].ox - self.nodes[i].ox,
                    self.nodes[i + 1].oy - self.nodes[i].oy,
                )
                self.links.append((i, i + 1, rest)) #now i learned the double brackets thing
    def step(self, dt, game, cfg):
        rho = cfg["fluid_rho"]
        wind_x = cfg["wind_x"]
        rel_vx = game.vx - wind_x
        rel_vy = game.vy
        speed = math.hypot(rel_vx, rel_vy)
        drag_mag = game.drag_coeff * rho * game.area_factor * speed + 0.35 * rho
        fx_drag = -drag_mag * rel_vx
        fy_drag = -drag_mag * rel_vy
        ax = fx_drag / game.mass_factor
        ay = (cfg["gravity"] * game.mass_factor) + (fy_drag / game.mass_factor)
        game.vx += ax * dt
        game.vy += ay * dt
        game.player_x += game.vx * dt
        game.player_y += game.vy * dt
        if game.player_x < 40:
            game.player_x = 40
            game.vx = max(0, game.vx)
        elif game.player_x > WIDTH - 40:
            game.player_x = WIDTH - 40
            game.vx = min(0, game.vx)
        stiffness = 140
        damping = 10
        for node in self.nodes:
            n_rel_vx = node.vx - wind_x
            n_rel_vy = node.vy
            n_speed = math.hypot(n_rel_vx, n_rel_vy)
            n_drag = 0.0012 * rho * n_speed + 0.45 * rho
            target_x = game.player_x + node.ox
            target_y = game.player_y + node.oy
            n_ax = stiffness * (target_x - node.x) - damping * node.vx - n_drag * n_rel_vx
            n_ay = cfg["gravity"] * 0.85 + stiffness * (target_y - node.y) - damping * node.vy - n_drag * n_rel_vy # yeah ai copy pasted
            node.vx += n_ax * dt
            node.vy += n_ay * dt
            node.x += node.vx * dt
            node.y += node.vy * dt
            if node.y > GROUND_Y:
                node.y = GROUND_Y
                node.vy *= -0.25
                node.vx *= 0.8
        for _ in range(3):
            for i, j, rest in self.links:
                a, b = self.nodes[i], self.nodes[j]
                dx = b.x - a.x
                dy = b.y - a.y
                dist = math.hypot(dx, dy) or 10**-6
                diff = (dist - rest) / dist * 0.5
                a.x += dx * diff
                a.y += dy * diff
                b.x -= dx * diff
                b.y -= dy * diff

class Game:
    def __init__(self):
        self.level_idx = 0
        self.rig = RigPhysics()
        self.cam_y = 0
        self.reset_level()
    def reset_level(self):
        cfg = LEVELS[self.level_idx]
        self.state = "DRAW"
        self.time_left = float(cfg["time"])
        self.player_x = float(DROP_START_X)
        self.player_y = float(cfg["drop_y"])
        self.vx = 0
        self.vy = 0.0
        self.strokes = []
        self.current_stroke = []
        self.is_drawing = False
        self.survived = False
        self.impact_speed = 0
        self.safe_limit = float(cfg["max_safe_vy"])
        self.drag_coeff = 0
        self.mass_factor = 1
        self.area_factor = 1
        self.rig.nodes.clear()
        self.rig.links.clear()
        self.cam_y = max(0, self.player_y - 260) if self.player_y < 260 else max(0, self.player_y - 460)
    def update_camera(self, dt):
        top_cam_y = min(0, float(LEVELS[self.level_idx]["drop_y"]) - 260)
        if self.state == "DRAW":
            desired_cam_y = top_cam_y
        else:
            start_y = float(LEVELS[self.level_idx]["drop_y"]) # two things i have to think a lot now naming a variable and also juz coding atp
            end_y = float(GROUND_Y - 32)
            progress = max(0, min(1, (self.player_y - start_y) / max(1, end_y - start_y)))
            desired_cam_y = top_cam_y * (1 - progress)
        self.cam_y += (desired_cam_y - self.cam_y) * min(1, dt * 5)
    def start_drop(self):
        self.state = "DROP"
        self.is_drawing = False
        if len(self.current_stroke) > 1:
            self.strokes.append(self.current_stroke)
        self.current_stroke = []
        self.strokes = [s for s in self.strokes if len(s) > 1]
        self.drag_coeff, cushion, self.mass_factor, self.area_factor = compute_contraption_stats(self.strokes)
        self.safe_limit = LEVELS[self.level_idx]["max_safe_vy"] + cushion
        self.rig.build_from_strokes(self.strokes, self.player_x, self.player_y)
game = Game()
running = True
while running:
    dt = min(clock.tick(60) / 1000, 0.05)
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
                rel_pt = (
                    event.pos[0] - game.player_x,
                    event.pos[1] + game.cam_y - game.player_y,
                )
                dist_from_center = math.hypot(rel_pt[0], rel_pt[1])
                if dist_from_center <= DRAW_RADIUS:
                    if dist_from_center <= ANCHOR_RADIUS:
                        rel_pt = (0, 0)
                    game.is_drawing = True
                    game.current_stroke = [rel_pt]
            elif event.type == pygame.MOUSEMOTION and game.is_drawing:
                if pygame.mouse.get_pressed()[0]:
                    rel_pt = (
                        event.pos[0] - game.player_x,
                        event.pos[1] + game.cam_y - game.player_y,
                    )
                    if math.hypot(rel_pt[0], rel_pt[1]) <= DRAW_RADIUS:
                        game.current_stroke.append(rel_pt)
                    else:
                        game.is_drawing = False
                        if len(game.current_stroke) > 1:
                            game.strokes.append(game.current_stroke)
                        game.current_stroke = []
                else:
                    game.is_drawing = False
                    if len(game.current_stroke) > 1:
                        game.strokes.append(game.current_stroke)
                    game.current_stroke = []
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1 and game.is_drawing:
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
        game.rig.step(dt, game, cfg)
        if game.player_y + 32 >= GROUND_Y:
            game.player_y = GROUND_Y - 32
            game.impact_speed = math.hypot(game.vx, game.vy)
            game.survived = game.impact_speed <= game.safe_limit
            game.state = "RESULT"
    game.update_camera(dt)
    cam_y = game.cam_y
    for c in clouds:
        c["x"] += (c["speed"] + cfg["wind_x"] * 0.4) * dt
        cw = c["surf"].get_width()
        if c["x"] > WIDTH + cw:
            c["x"] = -cw
        elif c["x"] < -cw:
            c["x"] = WIDTH + cw
    screen.fill((135, 200, 235)) #the best colour choice ig for a sky
    for c in clouds:
        screen.blit(c["surf"], (int(c["x"]), int(c["y"] - cam_y * 0.35)))
    ground_screen_y = int(GROUND_Y - cam_y)
    if ground_screen_y < HEIGHT:
        pygame.draw.rect(screen, (65, 150, 75), (0, ground_screen_y, WIDTH, HEIGHT - ground_screen_y))
    cliff_scale = cfg["cliff_height"] / cliff_img.get_height()
    cliff_w = int(cliff_img.get_width() * cliff_scale)
    scaled_cliff = pygame.transform.smoothscale(cliff_img, (cliff_w, cfg["cliff_height"]))
    cliff_rect = scaled_cliff.get_rect(bottomright=(DROP_START_X + 152, ground_screen_y))
    screen.blit(scaled_cliff, cliff_rect)
    player_screen_x = int(game.player_x)
    player_screen_y = int(game.player_y - cam_y)
    if game.state == "DRAW":
        all_visible_strokes = game.strokes + ([game.current_stroke] if game.current_stroke else [])
        for stroke in all_visible_strokes:
            if len(stroke) > 1:
                world_pts = [
                    (game.player_x + dx, game.player_y + dy - cam_y)
                    for dx, dy in stroke
                ]
                pygame.draw.lines(screen, (30, 30, 35), False, world_pts, 5)
    else:
        for i, j, _ in game.rig.links:
            na, nb = game.rig.nodes[i], game.rig.nodes[j]
            pygame.draw.line(screen, (30, 30, 35), (na.x, na.y - cam_y), (nb.x, nb.y - cam_y), 5) #im laughing my ahh off my letter choice here is "na" 
    sprite_rect = player_img.get_rect(center=(player_screen_x, player_screen_y))
    screen.blit(player_img, sprite_rect)
    if game.state == "DRAW":
        pygame.draw.circle(
            screen, (255, 255, 255), (player_screen_x, player_screen_y), DRAW_RADIUS, 2
        )
    lvl_txt = FONT_MED.render(f"level {cfg['level']} / {len(LEVELS)} | wind: {cfg['wind_x']:+.0f}", True, (20, 20, 20))
    screen.blit(lvl_txt, (20, 15))
    if game.state == "DRAW":
        timer_color = (200, 30, 30) if game.time_left <= 3 else (20, 20, 20)
        timer_txt = FONT_BIG.render(f"go ahead and DRAW! {game.time_left:.1f}s", True, timer_color)
        hint_txt = FONT_SMALL.render("drag mouse inside the ring to build your random ahh structure and[space] for drop", True, (20, 20, 20))
        screen.blit(timer_txt, (WIDTH // 2 - timer_txt.get_width() // 2, 15))
        screen.blit(hint_txt, (WIDTH // 2 - hint_txt.get_width() // 2, 65))
    elif game.state == "DROP":
        spd_txt = FONT_MED.render(f"fall speed: {int(math.hypot(game.vx, game.vy))} px/s (Safe <= {int(game.safe_limit)})", True, (20, 20, 20))
        screen.blit(spd_txt, (WIDTH // 2 - spd_txt.get_width() // 2, 20))
    elif game.state == "RESULT":
        status = "survived!" if game.survived else "splat! womp womp"
        color = (20, 140, 40) if game.survived else (200, 30, 30)
        res_txt = FONT_BIG.render(status, True, color)
        detail_txt = FONT_MED.render(
            f"impact: {int(game.impact_speed)} px/s |    safelimit: {int(game.safe_limit)} px/s",
            True,
            (20, 20, 20),
        )
        next_instruction = "press [enter] for next level " if game.survived else "press r to retry"
        instruction_txt = FONT_SMALL.render(next_instruction, True, (20, 20, 20))
        screen.blit(res_txt, (WIDTH // 2 - res_txt.get_width() // 2, 180))
        screen.blit(detail_txt, (WIDTH // 2 - detail_txt.get_width() // 2, 235))
        screen.blit(instruction_txt, (WIDTH // 2 - instruction_txt.get_width() // 2, 275)) #ok im writing instruction as prompt as thats the lalternative ugghh dont ask why i chose instruction over prompt
    pygame.display.flip()
pygame.quit()


