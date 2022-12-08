import sys
import math
import random
import time
import os

import pygame
from pygame.locals import *

import scripts.spritesheet_loader as spritesheet_loader
import scripts.tile_map as tile_map
import scripts.anim_loader as anim_loader
import scripts.particles as particles_m
from scripts.entity import Entity
import scripts.text as text
from scripts.clip import clip

TILE_SIZE = 12

pygame.mixer.pre_init(44100, -16, 2, 512)
pygame.init()
pygame.display.set_caption("Soul Knight")
screen = pygame.display.set_mode((900, 600), pygame.SCALED + pygame.RESIZABLE)
pygame.mouse.set_visible(False)
display = pygame.Surface((300, 200))
clock = pygame.time.Clock()

spritesheets, spritesheets_data = spritesheet_loader.load_spritesheets(
    "data/images/tilesets/"
)
level_map = tile_map.TileMap((TILE_SIZE, TILE_SIZE), (300, 200))
level_name = "level_1"
level_map.load_map(level_name + ".json")

level_spawns = {
    "debug": [180, 50],
    "level_1": [180, 50],
    "level_2": [350, 80],
    "level_3": [350, 362],
    "level_4": [350, 202],
}

bounded = {
    "debug": False,
    "level_1": True,
    "level_2": True,
    "level_3": True,
    "level_4": False,
}

auto_return = {
    "debug": True,
    "level_1": True,
    "level_2": False,
    "level_3": False,
    "level_4": True,
}

sounds = {
    k.split(".")[0]: pygame.mixer.Sound("data/sfx/" + k) for k in os.listdir("data/sfx")
}
sounds["eye_shoot"].set_volume(0.7)
sounds["jump"].set_volume(0.3)


def reload_level(restart_audio=True):
    global player, projectiles, particles, scroll_target, events, soul_mode, level_time, player_mana, level_map, player_message, zoom, death, next_level, door, ready_to_exit
    level_map.load_map(level_name + ".json")
    player.pos = level_spawns[level_name].copy()
    soul.pos = level_spawns[level_name].copy()
    player.rotation = 0
    scroll_target = player.pos
    true_scroll = [
        player.center[0] - display.get_width() // 2,
        player.center[1] - display.get_height() // 2,
    ]
    zoom = 10
    events = {
        "lv1": 0,
        "lv1mana": 0,
        "lv1note": 0,
        "lv2timer": 0,
        "lv3timer": 0,
    }
    soul_mode = 0
    level_time = 0
    player_mana = 1
    death = 0
    next_level = False
    ready_to_exit = False
    player_message = [0, "", ""]
    if level_name == "level_1":
        global tutorial, tutorial_2
        tutorial = 0
        tutorial_2 = -1

    projectiles = []
    particles = []

    if level_name != "level_1":
        door = None

    if restart_audio:
        if level_name == "level_3":
            pygame.mixer.music.load("data/music_2.wav")
            pygame.mixer.music.play(-1)
        else:
            pygame.mixer.music.load("data/music_1.wav")
            pygame.mixer.music.play(-1)


def advance(pos, rot, amt):
    pos[0] += math.cos(rot) * amt
    pos[1] += math.sin(rot) * amt
    return pos


def render_mana(loc, size=[2, 3], color1=(255, 255, 255), color2=(12, 230, 242)):
    global game_time
    points = []
    for i in range(8):
        points.append(
            advance(
                loc.copy(),
                game_time / 30 + i / 8 * math.pi * 2,
                (math.sin((game_time * math.sqrt(i)) / 20) * size[0] + size[1]),
            )
        )
    pygame.draw.polygon(display, color1, points)
    pygame.draw.polygon(display, color2, points, 1)


def particle_burst(loc, amt):
    global particles
    for i in range(amt):
        angle = random.randint(1, 360)
        speed = random.randint(20, 80) / 10
        vel = [math.cos(angle) * speed, math.sin(angle) * speed]
        particles.append(
            particles_m.Particle(
                loc[0],
                loc[1],
                "light",
                vel,
                0.8,
                2 + random.randint(0, 20) / 10,
                custom_color=(255, 255, 255),
            )
        )


animations = anim_loader.AnimationManager()

proj_img = pygame.image.load("data/images/projectile.png").convert()
proj_img.set_colorkey((0, 0, 0))
door_img = pygame.image.load("data/images/door.png").convert()
door_img.set_colorkey((0, 0, 0))

projectiles = []

particles_m.load_particle_images("data/images/particles")
particles = []

sparks = []

font = text.Font("data/fonts/small_font.png", (255, 255, 255))
blue_font = text.Font("data/fonts/small_font.png", (0, 152, 219))
red_font = text.Font("data/fonts/small_font.png", (244, 89, 120))
black_font = text.Font("data/fonts/small_font.png", (0, 0, 1))

player = Entity(animations, level_spawns[level_name], (7, 13), "player")
soul = Entity(animations, level_spawns[level_name], (7, 13), "soul")
player_mana = 1
soul.offset = [-1, -1]
player_velocity = [0, 0]
air_timer = 0

true_scroll = [
    player.center[0] - display.get_width() // 2,
    player.center[1] - display.get_height() // 2,
]
scroll = true_scroll.copy()
scroll_target = player.pos
zoom = 1

left = False
right = False
up = False
down = False

game_time = 0
level_time = 0
death = 0
tutorial = 0
tutorial_2 = -1
events = {
    "lv1": 0,
    "lv1mana": 0,
    "lv1note": 0,
    "lv2timer": 0,
    "lv3timer": 0,
}
next_level = False

soul_mode = 0

player_message = [0, "", ""]
player_bubble_size = 0
player_bubble_positions = [[0, 0], [0, 0], [0, 0]]

dt = 1
last_time = time.time()

door = (728, 60)
ready_to_exit = False

map_transition = 0

eye_target_height = 30
eye_height = 30

pygame.mixer.music.load("data/music_1.wav")
pygame.mixer.music.play(-1)

while True:
    display.fill((20, 19, 39))

    game_time += 1
    level_time += 1
    if death:
        death += 1
        if death > 70:
            if map_transition == 0:
                map_transition = 1

    if map_transition:
        last = map_transition
        map_transition += dt
        if (last < 60) and (map_transition >= 60):
            if next_level:
                level_n = int(level_name.split("_")[-1])
                level_name = level_name.split("_")[0] + "_" + str(level_n + 1)
            reload_level(next_level)
        if map_transition > 120:
            map_transition = 0

    b_points = [[0, 16]]
    b_points += [
        [
            display.get_width() / 30 * (i + 1)
            + math.sin((game_time + i * 120) / 4) * 8,
            16 + math.sin((game_time + i * 10) / 10) * 4,
        ]
        for i in range(29)
    ]
    b_points += [[display.get_width(), 16], [display.get_width(), 0], [0, 0]]
    b2_points = [[0, 16]]
    b2_points += [
        [
            display.get_width() / 30 * (i + 1)
            + math.sin((game_time + i * 120 - scroll[0] * 0.5) / 10) * 8,
            16 + math.sin((game_time + i * 10) / 10) * 4,
        ]
        for i in range(29)
    ]
    b2_points += [[display.get_width(), 16], [display.get_width(), 0], [0, 0]]
    b2_points = [[display.get_width() - p[0], p[1] * 3] for p in b2_points]
    back_surf = pygame.Surface((display.get_width(), 72))
    pygame.draw.polygon(back_surf, (15, 10, 24), b2_points)
    back_surf.set_colorkey((0, 0, 0))
    display.blit(back_surf, (0, 0))
    display.blit(
        pygame.transform.flip(back_surf, False, True), (0, display.get_height() - 72)
    )

    if (not map_transition) or (map_transition > 60):
        zoom += (1 - zoom) / 7
        if abs(1 - zoom) < 0.005:
            zoom = 1
    else:
        zoom += (5 - zoom) / 50

    if abs(int(scroll_target[0]) - display.get_width() // 2 - 3 - true_scroll[0]) < 0.5:
        true_scroll[0] = int(scroll_target[0]) - display.get_width() // 2 - 3
    else:
        true_scroll[0] += (
            (int(scroll_target[0]) - display.get_width() // 2 - 3 - true_scroll[0])
            / 20
            * dt
        )
    if abs(scroll_target[1] - display.get_height() // 2 - 5 - true_scroll[1]) <= 1:
        true_scroll[1] = int(scroll_target[1]) - display.get_height() // 2 - 5
    else:
        true_scroll[1] += (
            (scroll_target[1] - display.get_height() // 2 - 5 - true_scroll[1])
            / 20
            * dt
        )
    scroll = [int(true_scroll[0]), int(true_scroll[1])]
    if bounded[level_name]:
        size = [int(display.get_width() / zoom), int(display.get_height() / zoom)]
        zoom_offset = [
            (display.get_width() - size[0]) // 2,
            (display.get_height() - size[1]) // 2,
        ]
        scroll[0] = max(
            level_map.left * TILE_SIZE + TILE_SIZE * 3 - zoom_offset[0],
            min(
                level_map.right * TILE_SIZE
                - display.get_width()
                - TILE_SIZE * 2
                + zoom_offset[0],
                scroll[0],
            ),
        )
        scroll[1] = max(
            level_map.top * TILE_SIZE + TILE_SIZE * 3 - zoom_offset[1],
            min(
                level_map.bottom * TILE_SIZE
                - display.get_height()
                - TILE_SIZE * 4
                + zoom_offset[1],
                scroll[1],
            ),
        )

    if door:
        display.blit(door_img, (door[0] - scroll[0], door[1] - scroll[1]))
        if random.randint(1, 7) == 1:
            particles.append(
                particles_m.Particle(
                    door[0] + 6,
                    door[1] + 9,
                    "red_light",
                    [random.randint(0, 10) / 10 - 0.5, random.randint(0, 10) / 10 - 2],
                    0.1,
                    3.5 + random.randint(0, 20) / 10,
                    custom_color=(255, 255, 255),
                )
            )
        if player.get_distance([door[0] + 6, door[1] + 9]) < 5:
            if map_transition == 0:
                pygame.mixer.music.fadeout(500)
                map_transition = 1
                next_level = True
                sounds["door"].play()

    render_list = level_map.get_visible(scroll)
    collideables = []
    for layer in render_list:
        for tile in layer:
            offset = [0, 0]
            if tile[1][0] in spritesheets_data:
                tile_id = str(tile[1][1]) + ";" + str(tile[1][2])
                if tile_id in spritesheets_data[tile[1][0]]:
                    if "tile_offset" in spritesheets_data[tile[1][0]][tile_id]:
                        offset = spritesheets_data[tile[1][0]][tile_id]["tile_offset"]
            if tile[1][0] == "ground":
                if collideables == []:
                    if not death:
                        player.render(display, scroll)
                collideables.append(
                    pygame.Rect(tile[0][0], tile[0][1], TILE_SIZE, TILE_SIZE)
                )
            if tile[1][0] == "torches":
                if random.randint(1, 6) == 1:
                    particles.append(
                        particles_m.Particle(
                            tile[0][0] + 6,
                            tile[0][1] + 4,
                            "light",
                            [
                                random.randint(0, 10) / 10 - 0.5,
                                random.randint(0, 10) / 10 - 2,
                            ],
                            0.1,
                            3 + random.randint(0, 20) / 10,
                            custom_color=(255, 255, 255),
                        )
                    )
                torch_sin = math.sin((tile[0][1] % 100 + 200) / 300 * game_time * 0.01)
                particles_m.blit_center_add(
                    display,
                    particles_m.circle_surf(
                        15 + (torch_sin + 3) * 8.5,
                        (
                            4 + (torch_sin + 4) * 0.3,
                            8 + (torch_sin + 4) * 0.5,
                            18 + (torch_sin + 4) * 0.9,
                        ),
                    ),
                    (tile[0][0] - scroll[0] + 6, tile[0][1] - scroll[1] + 4),
                )
                particles_m.blit_center_add(
                    display,
                    particles_m.circle_surf(
                        9 + (torch_sin + 3) * 4,
                        (
                            4 + (torch_sin * 1.3 + 4) * 0.3,
                            8 + (torch_sin + 4) * 0.5,
                            18 + (torch_sin + 4) * 0.9,
                        ),
                    ),
                    (tile[0][0] - scroll[0] + 6, tile[0][1] - scroll[1] + 4),
                )
            if (tile[1][0] == "decorations") and (tile[1][1] == 0):
                if random.randint(1, 2) == 1:
                    p_offset = random.choice([[-8, 1], [8, 1], [4, 4], [-4, 4]])
                    particles.append(
                        particles_m.Particle(
                            tile[0][0] + TILE_SIZE + p_offset[0],
                            tile[0][1] + TILE_SIZE * 1.5 + p_offset[1],
                            "light",
                            [
                                random.randint(0, 10) / 10 - 0.5,
                                random.randint(0, 10) / 10 - 2,
                            ],
                            0.1,
                            4 + random.randint(0, 20) / 10,
                            custom_color=(255, 255, 255),
                        )
                    )
                torch_sin = math.sin((tile[0][1] % 100 + 200) / 300 * game_time * 0.01)
                particles_m.blit_center_add(
                    display,
                    particles_m.circle_surf(
                        15 + (torch_sin + 3) * 8.5,
                        (
                            4 + (torch_sin + 4) * 0.4,
                            8 + (torch_sin + 4) * 0.7,
                            18 + (torch_sin + 4) * 1.3,
                        ),
                    ),
                    (
                        tile[0][0] - scroll[0] + TILE_SIZE,
                        tile[0][1] - scroll[1] + TILE_SIZE * 1.5,
                    ),
                )
                particles_m.blit_center_add(
                    display,
                    particles_m.circle_surf(
                        9 + (torch_sin + 3) * 4,
                        (
                            4 + (torch_sin * 1.3 + 4) * 0.4,
                            8 + (torch_sin + 4) * 0.7,
                            18 + (torch_sin + 4) * 1.3,
                        ),
                    ),
                    (
                        tile[0][0] - scroll[0] + TILE_SIZE,
                        tile[0][1] - scroll[1] + TILE_SIZE * 1.5,
                    ),
                )
            if tile[1][0] != "mana":
                img = spritesheet_loader.get_img(spritesheets, tile[1])
                display.blit(
                    img,
                    (
                        math.floor(tile[0][0] - scroll[0] + offset[0]),
                        math.floor(tile[0][1] - scroll[1] + offset[1]),
                    ),
                )
            else:
                render_mana([tile[0][0] + 6 - scroll[0], tile[0][1] + 6 - scroll[1]])
                torch_sin = math.sin((tile[0][1] % 100 + 200) / 300 * game_time * 0.01)
                particles_m.blit_center_add(
                    display,
                    particles_m.circle_surf(
                        15 + (torch_sin + 3) * 8.5,
                        (
                            4 + (torch_sin + 4) * 0.3,
                            8 + (torch_sin + 4) * 0.5,
                            18 + (torch_sin + 4) * 0.9,
                        ),
                    ),
                    (tile[0][0] - scroll[0] + 6, tile[0][1] - scroll[1] + 4),
                )
                particles_m.blit_center_add(
                    display,
                    particles_m.circle_surf(
                        9 + (torch_sin + 3) * 4,
                        (
                            4 + (torch_sin * 1.3 + 4) * 0.3,
                            8 + (torch_sin + 4) * 0.5,
                            18 + (torch_sin + 4) * 0.9,
                        ),
                    ),
                    (tile[0][0] - scroll[0] + 6, tile[0][1] - scroll[1] + 4),
                )

    player.update(1 / 60 * dt)
    air_timer += 1

    if not map_transition:
        player_velocity[1] = min(player_velocity[1] + 0.23 * dt, 5)
    movement = player_velocity.copy()
    if not death and not soul_mode and not map_transition:
        if right:
            movement[0] += 1.5
        if left:
            movement[0] -= 1.5
    if death:
        collideables = []
        movement[0] = 1
        player.rotation -= 10
    if death == 2:
        player_velocity[1] = -7
    movement[0] *= min(dt, 3)
    movement[1] *= dt
    movement[1] = min(8, movement[1])
    if not map_transition:
        collisions = player.move(movement, collideables)
    if collisions["top"] or collisions["bottom"]:
        player_velocity[1] = 0
    if collisions["bottom"]:
        air_timer = 0

    if air_timer > 3:
        player.set_action("jump")
    elif movement[0] != 0:
        player.set_action("run")
    else:
        player.set_action("idle")
        if soul_mode:
            player.set_action("idle", True)

    if movement[0] > 0:
        player.flip[0] = False
    if movement[0] < 0:
        player.flip[0] = True

    if soul_mode:
        player.opacity = 120
        movement = [0, 0]
        if right:
            movement[0] += 0.75 * dt
        if left:
            movement[0] -= 0.75 * dt
        if up:
            movement[1] -= 0.75 * dt
        if down:
            movement[1] += 0.75 * dt
        soul_mode += max(dt, 0.3)
        if auto_return[level_name]:
            if soul_mode > 240:
                soul_mode = 0
                sounds["exit_soul"].play()
                particle_burst(player.center, 50)
                player.pos = soul.pos.copy()
                particle_burst(player.center, 50)
                scroll_target = player.pos
                player_velocity[1] = 0
        soul.move(movement, collideables)
        if soul.pos[0] < scroll[0]:
            soul.pos[0] = scroll[0]
        if soul.pos[0] > scroll[0] + display.get_width():
            soul.pos[0] = scroll[0] + display.get_width()
        if soul.pos[1] < scroll[1]:
            soul.pos[1] = scroll[1]
        if soul.pos[1] > scroll[1] + display.get_height():
            soul.pos[1] = scroll[1] + display.get_height()
        if random.randint(1, 3) == 1:
            particles.append(
                particles_m.Particle(
                    soul.pos[0] + 3,
                    soul.pos[1] + 4,
                    "light",
                    [random.randint(0, 10) / 10 - 0.5, random.randint(0, 10) / 10 + 1],
                    0.2,
                    3 + random.randint(0, 20) / 10,
                    custom_color=(255, 255, 255),
                )
            )
        torch_sin = math.sin((soul.center[1] % 100 + 200) / 300 * game_time * 0.1)
        particles_m.blit_center_add(
            display,
            particles_m.circle_surf(
                7 + (torch_sin + 3) * 3,
                (
                    4 + (torch_sin + 4) * 0.3,
                    8 + (torch_sin + 4) * 0.5,
                    18 + (torch_sin + 4) * 0.9,
                ),
            ),
            (soul.center[0] - 1 - scroll[0], soul.center[1] - 4 - scroll[1]),
        )
        particles_m.blit_center_add(
            display,
            particles_m.circle_surf(
                5 + (torch_sin + 3) * 2,
                (
                    4 + (torch_sin * 1.3 + 4) * 0.3,
                    8 + (torch_sin + 4) * 0.5,
                    18 + (torch_sin + 4) * 0.9,
                ),
            ),
            (soul.center[0] - 1 - scroll[0], soul.center[1] - 4 - scroll[1]),
        )
        if tutorial_2 == 0:
            tutorial_2 = 1
    else:
        player.opacity = 255

    if level_map.tile_collide(player.center):
        tile = level_map.tile_collide(player.center)
        tile_center = [
            player.center[0] // TILE_SIZE * TILE_SIZE + TILE_SIZE // 2,
            player.center[1] // TILE_SIZE * TILE_SIZE + TILE_SIZE // 2,
        ]
        rm = None
        for layer in tile:
            if tile[layer][0] == "mana":
                sounds["mana_1"].play()
                sounds["mana_2"].play()
                player_mana += 1
                rm = layer
                for i in range(2):
                    sparks.append(
                        [
                            tile_center.copy(),
                            math.pi / 2 + math.pi * i,
                            10,
                            6,
                            (255, 255, 255),
                        ]
                    )
                    sparks.append(
                        [tile_center.copy(), math.pi * i, 6, 3, (255, 255, 255)]
                    )
                for i in range(20):
                    particles.append(
                        particles_m.Particle(
                            tile_center[0],
                            tile_center[1],
                            "light",
                            [
                                random.randint(0, 10) / 10 - 0.5,
                                (random.randint(0, 120) / 10 + 1)
                                * random.choice([-1, 1]),
                            ],
                            0.1,
                            2 + random.randint(0, 20) / 10,
                            custom_color=(255, 255, 255),
                        )
                    )
        if rm:
            del tile[rm]

    for event in pygame.event.get():
        if event.type == QUIT:
            pygame.quit()
            sys.exit()
        if event.type == KEYDOWN:
            if event.key == K_ESCAPE:
                pygame.quit()
                sys.exit()
            if event.key == K_RIGHT:
                right = True
                if not tutorial:
                    tutorial = 1
            if event.key == K_LEFT:
                left = True
            if event.key == K_DOWN:
                if not ready_to_exit:
                    if (
                        (level_name != "level_1")
                        or (events["lv1"] != 0)
                        and (not map_transition)
                    ):
                        if soul_mode == 0:
                            if player_mana > 0:
                                soul_mode = 1
                                sounds["enter_soul"].play()
                                soul.pos = player.pos.copy()
                                player.pos = player.pos.copy()
                                particle_burst(player.center, 50)
                                player_mana -= 1
                            else:
                                player_message = [200, "J'ai besoin de plus de mana!", ""]
                else:
                    player_message = [300, "J'ai besoin d'avancer...", ""]
                down = True
            if event.key == K_UP:
                if (
                    not death
                    and (air_timer < 5)
                    and not soul_mode
                    and not map_transition
                ):
                    sounds["jump"].play()
                    player_velocity[1] = -5.2
                    sparks.append(
                        [
                            list(player.rect.bottomleft),
                            math.pi * 0.9,
                            2 + random.randint(0, 10) / 10,
                            5,
                            (255, 255, 255),
                        ]
                    )
                    sparks.append(
                        [
                            list(player.rect.bottomright),
                            math.pi * 0.1,
                            2 + random.randint(0, 10) / 10,
                            5,
                            (255, 255, 255),
                        ]
                    )
                up = True
        if event.type == KEYUP:
            if event.key == K_RIGHT:
                right = False
            if event.key == K_LEFT:
                left = False
            if event.key == K_DOWN:
                down = False
            if event.key == K_UP:
                up = False

    if death:
        player.render(display, scroll)

    eye_base = [386, 220]
    if not soul_mode:
        eye_angle = player.get_angle(eye_base) + math.pi
    else:
        eye_angle = soul.get_angle(eye_base) + math.pi
    if level_name == "level_3":
        if 6200 < events["lv3timer"] < 6600:
            eye_base = [386 + random.randint(0, 8) - 4, 220 + random.randint(0, 8) - 4]
            eye_target_height = 24
        if random.randint(0, 180) == 0:
            eye_height = 2
        eye_height += (eye_target_height - eye_height) / 20
        eye_points = [
            [-20, 0],
            [-10, -eye_height * 0.4],
            [10, -eye_height * 0.4],
            [20, 0],
            [8, eye_height * 0.3],
            [-8, eye_height * 0.3],
        ]
        render_points = [
            [p[0] + eye_base[0] - scroll[0], p[1] + eye_base[1] - scroll[1]]
            for p in eye_points
        ]
        if events["lv3timer"] < 6800:
            pygame.draw.polygon(display, (255, 255, 255), render_points)
            eye_center = [eye_base[0] - scroll[0], eye_base[1] - scroll[1]]
            advance(eye_center, eye_angle, 4)
            if eye_height > 16:
                pygame.draw.circle(
                    display, (244, 89, 120), eye_center, 5 * (eye_height / 60 + 0.7)
                )
                pygame.draw.circle(
                    display, (0, 0, 0), eye_center, 4 * (eye_height / 60 + 0.7)
                )

    dt = (time.time() - last_time) * 60
    last_time = time.time()

    reset = False
    if level_name == "level_1":
        if not events["lv1note"] and player_mana:
            if (
                events["lv1mana"]
                and (player_bubble_size < 0.05)
                and (player_message[0] == 0)
                and (level_time > 1500)
            ):
                player_message = [320, "J'ai entendu dire que la sortie était en hauteur...", ""]
                events["lv1note"] = 1
        if (events["lv1note"] == 1) and player_mana:
            if (
                events["lv1mana"]
                and (player_bubble_size < 0.05)
                and (player_message[0] == 0)
                and (level_time > 2500)
            ):
                player_message = [500, "Je peux mieux me deplacer en ame.", ""]
                events["lv1note"] = 2
        if not events["lv1mana"]:
            if player.pos[0] > 530:
                player_message = [320, "J'ai besoin de mana pour refaire ca...", ""]
                events["lv1mana"] = 1

        if not events["lv1"]:
            if player.pos[0] > 446:
                events["lv1"] = 1
                for i in range(17):
                    vel = [-4, 0]
                    angle = math.atan2(vel[1], vel[0])
                    spawn = [
                        display.get_width() + scroll[0],
                        display.get_height() * i / 15 + scroll[1],
                    ]
                    for i in range(5):
                        sparks.append(
                            [
                                spawn.copy(),
                                angle + math.radians(random.randint(0, 80) - 40),
                                4 + random.randint(0, 30) / 10,
                                10,
                                (0, 0, 0),
                            ]
                        )
                    projectiles.append([spawn, vel, "enemy"])
                sounds["eye_shoot_large"].play()
        if events["lv1"]:
            if events["lv1"] != -1:
                events["lv1"] += dt
                if events["lv1"] > 33:
                    if not soul_mode:
                        dt = 0
                    else:
                        dt = 0.5
                    if tutorial_2 == -1:
                        tutorial_2 = 0
                if soul_mode > 20:
                    events["lv1"] = -1

    if level_name == "level_2":
        last = events["lv2timer"]
        events["lv2timer"] += dt
        if events["lv2timer"] < 6:
            player_message = [420, "Ca ressemble a un piege...", ""]
        if (last < 920) and (events["lv2timer"] >= 920):
            reset = True
            player_message = [420, "J'ai juste besoin de survivre pour l'instant.", ""]
        if (last < 1840) and (events["lv2timer"] >= 1840):
            reset = True
        if (last < 2750) and (events["lv2timer"] >= 2750):
            reset = True
        if 3050 < events["lv2timer"] < 3650:
            if (events["lv2timer"] % 250 < last % 250) or (
                events["lv2timer"] % 110 < last % 110
            ):
                dir = random.choice([-1, 1])
                offset = random.randint(0, 20) / 20
                for i in range(11):
                    i -= offset
                    vel = [4 * dir, 0]
                    angle = math.atan2(vel[1], vel[0])
                    if dir == -1:
                        spawn = [
                            display.get_width() + scroll[0],
                            display.get_height() * i / 8 + scroll[1],
                        ]
                    else:
                        spawn = [scroll[0], display.get_height() * i / 8 + scroll[1]]
                    for j in range(5):
                        sparks.append(
                            [
                                spawn.copy(),
                                angle + math.radians(random.randint(0, 80) - 40),
                                4 + random.randint(0, 30) / 10,
                                10,
                                (0, 0, 0),
                            ]
                        )
                    projectiles.append([spawn, vel, "enemy"])
                sounds["eye_shoot_large"].play()
        if (last < 3880) and (events["lv2timer"] >= 3880):
            reset = True
            player_message = [420, "Ouf, pas loin.", ""]
            door = (330, 372)
            ready_to_exit = True
            sounds["end_level"].play()
    if level_name == "level_3":
        last = events["lv3timer"]
        events["lv3timer"] += dt
        if events["lv3timer"] < 6:
            player_message = [200, "Oh oh...", ""]
        if 200 < events["lv3timer"] < 800:
            eye_target_height = 30
            if random.randint(0, 70) == 0:
                sounds["eye_shoot_large"].play()
                for i in range(5):
                    speed = random.randint(30, 40) / 10
                    angle = eye_angle + random.random() * math.pi / 4 - math.pi / 8
                    vel = [math.cos(angle) * speed, math.sin(angle) * speed]
                    spawn = eye_base.copy()
                    for i in range(3):
                        sparks.append(
                            [
                                spawn.copy(),
                                angle + math.radians(random.randint(0, 80) - 40),
                                4 + random.randint(0, 30) / 10,
                                10,
                                (0, 0, 0),
                            ]
                        )
                    projectiles.append([spawn, vel, "enemy"])
        elif 1300 < events["lv3timer"] < 1800:
            eye_target_height = 30
            if random.randint(0, 90) == 0:
                sounds["eye_shoot_large"].play()
                offset = random.random() * math.pi * 2
                for i in range(36):
                    speed = 3.5
                    angle = math.pi * 2 * i / 36 + offset
                    vel = [math.cos(angle) * speed, math.sin(angle) * speed]
                    spawn = eye_base.copy()
                    for i in range(3):
                        sparks.append(
                            [
                                spawn.copy(),
                                angle + math.radians(random.randint(0, 80) - 40),
                                4 + random.randint(0, 30) / 10,
                                10,
                                (0, 0, 0),
                            ]
                        )
                    projectiles.append([spawn, vel, "enemy"])
        elif 2500 < events["lv3timer"] < 3100:
            eye_target_height = 38
            if game_time % 10 == 0:
                sounds["eye_shoot"].play()
                offset = game_time / 600 * math.pi * 2
                for i in range(6):
                    speed = 3.5
                    angle = math.pi * 2 * i / 6 + offset
                    vel = [math.cos(angle) * speed, math.sin(angle) * speed]
                    spawn = eye_base.copy()
                    for i in range(3):
                        sparks.append(
                            [
                                spawn.copy(),
                                angle + math.radians(random.randint(0, 80) - 40),
                                7 + random.randint(0, 30) / 10,
                                5,
                                (0, 0, 0),
                            ]
                        )
                    projectiles.append([spawn, vel, "enemy"])
        elif 3600 < events["lv3timer"] < 4500:
            eye_target_height = 38
            if game_time % 17 == 0:
                sounds["eye_shoot"].play()
                for j in range(2):
                    if j == 0:
                        offset = game_time / 600 * math.pi * 2
                    else:
                        offset = -game_time / 600 * math.pi * 2
                    for i in range(6):
                        speed = 3.5
                        angle = math.pi * 2 * i / 6 + offset
                        vel = [math.cos(angle) * speed, math.sin(angle) * speed]
                        spawn = eye_base.copy()
                        for i in range(3):
                            sparks.append(
                                [
                                    spawn.copy(),
                                    angle + math.radians(random.randint(0, 80) - 40),
                                    7 + random.randint(0, 30) / 10,
                                    5,
                                    (0, 0, 0),
                                ]
                            )
                        projectiles.append([spawn, vel, "enemy"])
        elif 5200 < events["lv3timer"] < 5800:
            eye_target_height = 30
            if game_time % 3 == 0:
                sounds["eye_shoot"].play()
                offset = game_time / 600 * math.pi * 2
                for i in range(3):
                    speed = 3.5
                    angle = math.pi * 2 * i / 3 + offset
                    vel = [math.cos(angle) * speed, math.sin(angle) * speed]
                    spawn = eye_base.copy()
                    for i in range(3):
                        sparks.append(
                            [
                                spawn.copy(),
                                angle + math.radians(random.randint(0, 80) - 40),
                                7 + random.randint(0, 30) / 10,
                                5,
                                (0, 0, 0),
                            ]
                        )
                    projectiles.append([spawn, vel, "enemy"])
        else:
            eye_target_height = 4
        if (last < 1150) and (events["lv3timer"] >= 1150):
            reset = True
        if (last < 2300) and (events["lv3timer"] >= 2300):
            reset = True
        if (last < 3400) and (events["lv3timer"] >= 3400):
            reset = True
        if (last < 4800) and (events["lv3timer"] >= 4800):
            reset = True
        if (last < 6200) and (events["lv3timer"] >= 6200):
            sounds["shake"].play()
        if (last < 6800) and (events["lv3timer"] >= 6800):
            reset = True
            player_message = [200, "...", ""]
            door = (360, 360)
            sounds["end_level"].play()
            sounds["death"].play()
            ready_to_exit = True
            for i in range(35):
                sparks.append(
                    [
                        eye_base.copy(),
                        math.radians(random.randint(1, 360)),
                        7 + random.randint(0, 30) / 10,
                        8,
                        (255, 255, 255),
                    ]
                )
            for i in range(300):
                angle = random.randint(1, 360)
                speed = random.randint(70, 250) / 10
                vel = [math.cos(angle) * speed, math.sin(angle) * speed]
                particles.append(
                    particles_m.Particle(
                        eye_base[0],
                        eye_base[1],
                        "red_light",
                        vel,
                        0.2,
                        1.5 + random.randint(0, 20) / 10,
                        custom_color=(255, 255, 255),
                    )
                )
        if (last < 1200) and (events["lv3timer"] >= 1200):
            player_message = [200, "Il y en a plus?", ""]
    if reset:
        if soul_mode:
            soul_mode = 0
            sounds["exit_soul"].play()
            particle_burst(player.center, 50)
            player.pos = soul.pos.copy()
            particle_burst(player.center, 50)
            scroll_target = player.pos
            player_velocity[1] = 0

    if not soul_mode:
        r = player.rect
    else:
        r = pygame.Rect(soul.center[0] - 3, soul.center[1] - 7, 7, 7)
    for projectile in projectiles:
        if len(projectile) == 3:
            projectile.append(random.random() + 1)
        projectile[0][0] += projectile[1][0] * 0.2 * dt
        projectile[0][1] += projectile[1][1] * 0.2 * dt
        if not map_transition:
            if projectile[2] == "enemy":
                if not death:
                    if r.collidepoint(projectile[0]):
                        sounds["death"].play()
                        death = 1
                        soul_mode = 0
                        scroll_target = scroll_target.copy()
                        for i in range(30):
                            sparks.append(
                                [
                                    list(r.center),
                                    math.radians(random.randint(1, 360)),
                                    5 + random.randint(0, 30) / 10,
                                    4,
                                    (255, 255, 255),
                                ]
                            )
                        for i in range(120):
                            angle = random.randint(1, 360)
                            speed = random.randint(70, 250) / 10
                            vel = [math.cos(angle) * speed, math.sin(angle) * speed]
                            particles.append(
                                particles_m.Particle(
                                    r.center[0],
                                    r.center[1],
                                    "light",
                                    vel,
                                    0.4,
                                    2 + random.randint(0, 20) / 10,
                                    custom_color=(255, 255, 255),
                                )
                            )
                display.blit(
                    proj_img,
                    (
                        projectile[0][0] - scroll[0] - 2,
                        projectile[0][1] - scroll[1] - 2,
                    ),
                )
                particles_m.blit_center_add(
                    display,
                    particles_m.circle_surf(
                        3 + 3 * (math.sin(projectile[3] * game_time * 0.15) + 3),
                        (20, 6, 12),
                    ),
                    (projectile[0][0] - scroll[0], projectile[0][1] - scroll[1]),
                )
    if level_name != "level_3":
        projectiles = projectiles[-300:]
    else:
        projectiles = projectiles[-500:]

    if (
        (events["lv1"] or level_name != "level_1")
        and (not map_transition)
        and (events["lv3timer"] < 6300)
        and (level_name != "level_4")
    ):
        rate = 25
        if (level_name == "level_2") and (
            (240 < events["lv2timer"] < 840)
            or (1200 < events["lv2timer"] < 1760)
            or (2000 < events["lv2timer"] < 2600)
        ):
            rate = 6
        if random.randint(0, rate) == 0:
            vel = [random.randint(0, 20) / 10 - 1, 4]
            angle = math.atan2(vel[1], vel[0])
            spawn = [display.get_width() * random.random() + scroll[0], scroll[1]]
            for i in range(5):
                sparks.append(
                    [
                        spawn.copy(),
                        angle + math.radians(random.randint(0, 80) - 40),
                        4 + random.randint(0, 30) / 10,
                        6,
                        (0, 0, 0),
                    ]
                )
            projectiles.append([spawn, vel, "enemy"])
            sounds["eye_shoot"].play()

    for i, spark in sorted(enumerate(sparks), reverse=True):
        advance(spark[0], spark[1], spark[2] * dt)
        spark[2] -= 0.2 * dt
        if spark[2] < 0:
            sparks.pop(i)
            continue
        point_list = [
            advance(spark[0].copy(), spark[1], spark[2] * spark[3]),
            advance(spark[0].copy(), spark[1] + math.pi / 2, spark[2] * spark[3] * 0.1),
            advance(spark[0].copy(), spark[1] + math.pi, spark[2] * spark[3] * 0.6),
            advance(spark[0].copy(), spark[1] - math.pi / 2, spark[2] * spark[3] * 0.1),
        ]
        point_list = [[p[0] - scroll[0], p[1] - scroll[1]] for p in point_list]
        pygame.draw.polygon(display, spark[4], point_list)

    fog_surf = pygame.Surface((display.get_width(), 24))
    pygame.draw.polygon(fog_surf, (0, 2, 4), b_points)
    fog_surf.set_alpha(150)
    fog_surf.set_colorkey((0, 0, 0))
    display.blit(pygame.transform.flip(fog_surf, True, False), (0, -6))
    display.blit(fog_surf, (0, 0))
    display.blit(
        pygame.transform.flip(fog_surf, True, True), (0, display.get_height() - 24 + 6)
    )
    display.blit(
        pygame.transform.flip(fog_surf, False, True), (0, display.get_height() - 24)
    )
    side_fog = pygame.transform.scale(
        pygame.transform.rotate(fog_surf, 90), (24, display.get_height())
    )
    display.blit(pygame.transform.flip(side_fog, False, True), (-6, 0))
    display.blit(side_fog, (0, 0))
    display.blit(
        pygame.transform.flip(side_fog, True, True), (display.get_width() - 24, 0)
    )
    display.blit(
        pygame.transform.flip(side_fog, True, False), (display.get_width() - 24 + 6, 0)
    )

    for i, particle in sorted(enumerate(particles), reverse=True):
        alive = particle.update(0.1 * dt)
        particle.draw(display, scroll)
        if particle.type == "light":
            particles_m.blit_center_add(
                display,
                particles_m.circle_surf(
                    5
                    + particle.time_left
                    * 0.5
                    * (math.sin(particle.random_constant * game_time * 0.01) + 3),
                    (
                        1 + particle.time_left * 0.2,
                        4 + particle.time_left * 0.4,
                        8 + particle.time_left * 0.6,
                    ),
                ),
                (particle.x - scroll[0], particle.y - scroll[1]),
            )
        if particle.type == "red_light":
            particles_m.blit_center_add(
                display,
                particles_m.circle_surf(
                    5
                    + particle.time_left
                    * 0.5
                    * (math.sin(particle.random_constant * game_time * 0.01) + 3),
                    (
                        8 + particle.time_left * 0.6,
                        1 + particle.time_left * 0.2,
                        4 + particle.time_left * 0.4,
                    ),
                ),
                (particle.x - scroll[0], particle.y - scroll[1]),
            )
        if not alive:
            particles.pop(i)

    if door:
        particles_m.blit_center_add(
            display,
            particles_m.circle_surf(
                7 + 4 * (math.sin(game_time * 0.15) + 3), (20, 6, 12)
            ),
            (door[0] + 6 - scroll[0], door[1] + 9 - scroll[1]),
        )
        render_mana(
            [door[0] - scroll[0] + 6, door[1] - scroll[1] + 9],
            size=[2, 3],
            color1=(0, 0, 1),
            color2=(244, 89, 120),
        )

    if soul_mode:
        soul.render(display, scroll)

    if player_message[0] and not death:
        player_message[0] -= 1
        if player_message[0] % 3 == 0:
            if player_message[2] != player_message[1]:
                sounds["thought"].play()
            player_message[2] = player_message[1][: len(player_message[2]) + 1]
        player_bubble_size += (1 - player_bubble_size) / 5
    else:
        player_bubble_size += (0 - player_bubble_size) / 5
        player_message[2] = player_message[2][:-1]
    relative_positions = [
        [-4, -3],
        [-14, -7],
        [-30, -17],
    ]
    for i, p in enumerate(player_bubble_positions):
        if not soul_mode:
            p[0] += (player.pos[0] + relative_positions[i][0] - p[0]) / (3 + i * 3)
            p[1] += (player.pos[1] + relative_positions[i][1] - p[1]) / (3 + i * 3)
        else:
            p[0] += (soul.pos[0] + relative_positions[i][0] - p[0]) / (3 + i * 3)
            p[1] += (soul.pos[1] + relative_positions[i][1] - p[1]) / (3 + i * 3)
    if player_bubble_size > 0.05:
        for i, p in enumerate(player_bubble_positions):
            points = []
            if i == 2:
                i = 6
            for j in range(8):
                points.append(
                    advance(p.copy(), j / 8 * math.pi * 2, player_bubble_size * (i + 2))
                )
            points = [[p[0] - scroll[0], p[1] - scroll[1]] for p in points]
            if i == 6:
                for j, p2 in enumerate(points):
                    if (j < 2) or (j > 5):
                        p2[0] += font.width(player_message[1]) * player_bubble_size

            pygame.draw.polygon(display, (0, 0, 0), points)

            if i == 6:
                font.render(
                    player_message[2], display, [p[0] - scroll[0], p[1] - scroll[1] - 3]
                )

    if tutorial < 200:
        if tutorial != 0:
            tutorial += (display.get_width() - tutorial) / 7
        black_font.render(
            "utilisez les fleches pour bouger et sauter",
            display,
            (
                display.get_width() // 2
                + tutorial
                - font.width("utilisez les fleches pour bouger et sauter") // 2
                + 1,
                display.get_height() // 2 - 10,
            ),
        )
        blue_font.render(
            "utilisez les fleches pour bouger et sauter",
            display,
            (
                display.get_width() // 2
                + tutorial
                - font.width("utilisez les fleches pour bouger et sauter") // 2,
                display.get_height() // 2 - 11,
            ),
        )
        font.render(
            "utilisez les fleches pour bouger et sauter",
            display,
            (
                display.get_width() // 2
                + tutorial
                - font.width("utilisez les fleches pour bouger et sauter") // 2,
                display.get_height() // 2 - 12,
            ),
        )
    if tutorial_2 < 200:
        if tutorial_2 > 0:
            tutorial_2 += (display.get_width() - tutorial_2) / 7
        if tutorial_2 != -1:
            black_font.render(
                "utilisez la fleche du bas pour devenir une ame",
                display,
                (
                    display.get_width() // 2
                    + tutorial_2
                    - font.width("utilisez la fleche du bas pour devenir une ame") // 2
                    + 1,
                    display.get_height() // 2 - 10,
                ),
            )
            blue_font.render(
                "utilisez la fleche du bas pour devenir une ame",
                display,
                (
                    display.get_width() // 2
                    + tutorial_2
                    - font.width("utilisez la fleche du bas pour devenir une ame") // 2,
                    display.get_height() // 2 - 11,
                ),
            )
            font.render(
                "utilisez la fleche du bas pour devenir une ame",
                display,
                (
                    display.get_width() // 2
                    + tutorial_2
                    - font.width("utilisez la fleche du bas pour devenir une ame") // 2,
                    display.get_height() // 2 - 12,
                ),
            )
    if level_name == "level_4":
        black_font.render(
            "Merci d'avoir joue!",
            display,
            (
                display.get_width() // 2 - font.width("Merci d'avoir joue!") // 2 + 1,
                display.get_height() // 2 - 10,
            ),
        )
        blue_font.render(
            "Merci d'avoir joue!",
            display,
            (
                display.get_width() // 2 - font.width("Merci d'avoir joue!") // 2,
                display.get_height() // 2 - 11,
            ),
        )
        font.render(
            "Merci d'avoir joue!",
            display,
            (
                display.get_width() // 2 - font.width("Merci d'avoir joue!") // 2,
                display.get_height() // 2 - 12,
            ),
        )

    no_mana = ""
    if not player_mana:
        no_mana = "no "
    black_font.render(no_mana + "mana", display, (5, 6))
    if player_mana:
        blue_font.render(no_mana + "mana", display, (5, 5))
    else:
        red_font.render(no_mana + "mana", display, (5, 5))
    font.render(no_mana + "mana", display, (5, 4))

    for i in range(player_mana):
        render_mana([10 + i * 16, 18])

    if zoom == 1:
        screen.blit(pygame.transform.scale(display, screen.get_size()), (0, 0))
    else:
        size = [int(display.get_width() / zoom), int(display.get_height() / zoom)]
        screen.blit(
            pygame.transform.scale(
                clip(
                    display,
                    (display.get_width() - size[0]) // 2,
                    (display.get_height() - size[1]) // 2,
                    size[0],
                    size[1],
                ),
                screen.get_size(),
            ),
            (0, 0),
        )

    if map_transition:
        black_surf = pygame.Surface(display.get_size()).convert_alpha()
        if map_transition < 60:
            black_surf.set_alpha(map_transition / 60 * 255)
        else:
            black_surf.set_alpha((1 - (map_transition - 60) / 60) * 255)
        screen.blit(pygame.transform.scale(black_surf, screen.get_size()), (0, 0))
    pygame.display.update()
    clock.tick(60)
