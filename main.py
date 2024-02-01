import pygame
import math
import random

# constants
GRID_SIZE = (6, 13)
HIDDEN_ROWS = 1
GAME_SIZE = (1280, 720)
PUYO_COLORS = [pygame.Color(30, 30, 30), pygame.Color(80, 40, 40), pygame.Color(80, 80, 40), pygame.Color(40, 80, 40), pygame.Color(40, 40, 80)]

# frame data (src: https://puyonexus.com/wiki/Puyo_Puyo_Tsu/Frame_Data_Tables)
PUYO_FALL_TIME = 32
DAS = 8  # Delayed Auto Shift
ARR = 2  # Auto Repeat Rate


def collision_logic():
    return puyo_pos[1] >= GRID_SIZE[1] + HIDDEN_ROWS or other_puyo_pos()[1] >= GRID_SIZE[1] + HIDDEN_ROWS or board_at(puyo_pos) != 0 or board_at(other_puyo_pos()) != 0


def board_at(pos):
    return board_state[pos[0]][pos[1]]


def canMove(dx):
    return 0 <= puyo_pos[0] + dx < GRID_SIZE[0] and 0 <= other_puyo_pos()[0] + dx < GRID_SIZE[0] and board_at([puyo_pos[0] + dx, puyo_pos[1]]) == 0 and board_at([other_puyo_pos()[0] + dx, other_puyo_pos()[1]]) == 0


def other_puyo_pos():
    o = [i for i in puyo_pos]
    if rotation == 0:
        o[1] -= 1
    elif rotation == 1:
        o[0] += 1
    elif rotation == 2:
        o[1] += 1
    elif rotation == 3:
        o[0] -= 1
    return o


if __name__ == "__main__":
    pygame.init()
    running = True
    screen = pygame.display.set_mode(GAME_SIZE)
    clock = pygame.time.Clock()

    dt = 0  # everything will probably be frame-based but just in case
    puyo_pos = [2, 1]
    fall_timer = PUYO_FALL_TIME
    das_timers = [0, 0]
    das_active = [False, False]
    rotation_active = [True, True]
    cur_puyos = (random.randint(1, 4), random.randint(1, 4))
    rotation = 0  # 0-3, up-right-down-left probably
    board_state = [[0 for y in range(GRID_SIZE[1]+HIDDEN_ROWS)] for x in range(GRID_SIZE[0])]
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # ## INPUT STUFF GOES HERE ## #

        keys = pygame.key.get_pressed()
        for i in range(len(das_timers)):
            if das_timers[i] > 0:
                das_timers[i] -= 1
        if keys[pygame.K_LEFT]:
            if das_timers[0] == 0:
                if das_active[0]:
                    das_timers[0] = ARR
                else:
                    das_timers[0] = DAS
                    das_active[0] = True
                if canMove(-1):
                    puyo_pos[0] -= 1
        elif das_active[0]:
            das_active[0] = False
        if keys[pygame.K_RIGHT]:
            if das_timers[1] == 0:
                if das_active[1]:
                    das_timers[1] = ARR
                else:
                    das_timers[1] = DAS
                    das_active[1] = True
                if canMove(1):
                    puyo_pos[0] += 1
        elif das_active[1]:
            das_active[1] = False
        if keys[pygame.K_DOWN]:
            fall_timer -= 15

        # temporary reset board button
        if keys[pygame.K_r]:
            board_state = [[0 for y in range(GRID_SIZE[1] + HIDDEN_ROWS)] for x in range(GRID_SIZE[0])]

        # todo: rotation logic
        '''
        if keys[pygame.K_z] and rotation_active[0]:
            rotation = (rotation + 3) % 4
            rotation_active[0] = False
        elif not keys[pygame.K_z] and not rotation_active[0]:
            rotation_active[0] = True
        if keys[pygame.K_x] and rotation_active[1]:
            rotation = (rotation + 1) % 4
            rotation_active[1] = False
        elif not keys[pygame.K_x] and not rotation_active[1]:
            rotation_active[1] = True
        '''

        # ## LOGIC STUFF GOES HERE ## #

        fall_timer -= 1
        if fall_timer <= 0:
            fall_timer = PUYO_FALL_TIME
            puyo_pos[1] += 1

        if collision_logic():
            # print(puyo_pos)
            # print(other_puyo_pos)
            puyo_pos[1] -= 1
            board_state[puyo_pos[0]][puyo_pos[1]] = cur_puyos[0]
            board_state[other_puyo_pos()[0]][other_puyo_pos()[1]] = cur_puyos[1]
            # generate new puyo
            puyo_pos = [2, 1]
            cur_puyos = (random.randint(1, 4), random.randint(1, 4))

        # ## DRAW STUFF GOES HERE ## #

        screen.fill("black")
        # draw the grid
        square_size = math.floor((screen.get_height()*0.8)/GRID_SIZE[1])
        # thus,
        grid_pixelsize = (GRID_SIZE[0] * square_size, GRID_SIZE[1] * square_size)
        base_pos = ((screen.get_width() - grid_pixelsize[0])/2, (screen.get_height() - grid_pixelsize[1])/2)

        for y in range(HIDDEN_ROWS, GRID_SIZE[1] + HIDDEN_ROWS):
            ypos = base_pos[1] + square_size * (y - HIDDEN_ROWS)
            for x in range(GRID_SIZE[0]):
                xpos = base_pos[0] + square_size * x
                fill = PUYO_COLORS[board_state[x][y]]
                if x == puyo_pos[0] and y == puyo_pos[1]:
                    fill = PUYO_COLORS[cur_puyos[0]]
                elif x == other_puyo_pos()[0] and y == other_puyo_pos()[1]:
                    fill = PUYO_COLORS[cur_puyos[1]]
                pygame.draw.rect(screen, fill, pygame.Rect(xpos, ypos, square_size*0.9, square_size*0.9))

        pygame.display.flip()
        # print(board_state)
        dt = clock.tick(60) / 1000
    pygame.quit()
