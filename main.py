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
DROP_TIMES = [10, 5, 4, 3, 3, 3, 3, 2, 2, 2, 2, 2, 2, 2]
TIME_BETWEEN_PUYOS = 16

TIME_TO_POP = 48 # long animation...
GROUP_TO_POP = 4  # 4 is default ofc, but other numbers can be ""fun""


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


def rotate_logic(dir):
    global rotation
    # handles logic for rotations (mainly wall kicks, but also can't rotate once in a one wide well)
    # first do the rotation and pretend it's fine
    rotation = (rotation + dir) % 4
    # then check if it's fine
    # if the other puyo isn't in a wall right now, it's fine
    # print(other_puyo_pos()[1])
    if 0 <= other_puyo_pos()[0] < GRID_SIZE[0] and 0 <= other_puyo_pos()[1] < GRID_SIZE[1] + HIDDEN_ROWS and board_at(other_puyo_pos()) == 0:
        return
    # print("kicking (rotation =", rotation, ")")
    # if the rotation is 2 and we're colliding with something it must be something below, we can floor kick here
    if rotation == 2:
        puyo_pos[1] -= 1
        return
    # if the rotation is 1 or 3 then check the opposite direction; if it's clear, then move that way; otherwise, cancel the rotation
    if rotation == 1:
        if canMove(-1):
            puyo_pos[0] -= 1
        else:
            rotation = (rotation - dir) % 4
        return

    if rotation == 3:
        if canMove(1):
            puyo_pos[0] += 1
        else:
            rotation = (rotation - dir) % 4
        return

    # if somehow something else happens..... let's just cancel the rotation. be safe.
    rotation = (rotation - dir) % 4
    return


def puyos_need_drop():
    dropped = False
    for y in range(GRID_SIZE[1]+HIDDEN_ROWS - 2, -1, -1):
        for x in range(GRID_SIZE[0]):
            if board_at([x, y]) != 0 and board_at([x, y+1]) == 0:
                # get that puyo down from there!!
                board_state[x][y+1] = board_state[x][y]
                board_state[x][y] = 0
                dropped = True
    return dropped


def flag_pop_puyos():
    pop_count = 0
    for y in range(GRID_SIZE[1]+HIDDEN_ROWS):
        for x in range(GRID_SIZE[0]):
            if board_at([x, y]) != 0:
                # this is probably really bad but i dont know a better way to do it and i dont exactly wanna copy code off the internet and its a small enough field that it works fine!!
                current_group = board_at([x, y])
                group_size = 1
                checked_stack = [[x, y]]
                check_stack = [[x + 1, y], [x - 1, y], [x, y + 1], [x, y - 1]]
                while len(check_stack) > 0:
                    cur_check = check_stack.pop()
                    if 0 <= cur_check[0] < GRID_SIZE[0] and 0 <= cur_check[1] < GRID_SIZE[1] + HIDDEN_ROWS:
                        if board_at(cur_check) == current_group:
                            group_size += 1
                            checked_stack.append(cur_check)
                            new_additions = [[cur_check[0] + 1, cur_check[1]], [cur_check[0] - 1, cur_check[1]],
                                             [cur_check[0], cur_check[1] + 1], [cur_check[0], cur_check[1] - 1]]
                            for i in new_additions:
                                unique = True
                                for j in check_stack:
                                    if j[0] == i[0] and j[1] == i[1]:
                                        unique = False
                                for j in checked_stack:
                                    if j[0] == i[0] and j[1] == i[1]:
                                        unique = False
                                if unique:
                                    check_stack.append(i)
                # print(x, y, group_size)

                if group_size >= 4:
                    popping_board[x][y] = True
                    pop_count += 1
    return pop_count


def perform_pop_puyos():
    for y in range(GRID_SIZE[1] + HIDDEN_ROWS):
        for x in range(GRID_SIZE[0]):
            if popping_board[x][y]:
                board_state[x][y] = 0
                popping_board[x][y] = False


if __name__ == "__main__":
    pygame.init()
    running = True
    screen = pygame.display.set_mode(GAME_SIZE)
    clock = pygame.time.Clock()

    dt = 0  # everything will probably be frame-based but just in case
    puyo_pos = [2, 1]
    pop_delay = 0
    drop_delay = 0
    drop_step = 0
    fall_timer = PUYO_FALL_TIME
    das_timers = [0, 0]
    das_active = [False, False]
    rotation_active = [True, True]
    cur_puyos = (random.randint(1, 4), random.randint(1, 4))
    rotation = 0  # 0-3, up-right-down-left probably
    board_state = [[0 for y in range(GRID_SIZE[1]+HIDDEN_ROWS)] for x in range(GRID_SIZE[0])]
    popping_board = [[False for y in range(GRID_SIZE[1] + HIDDEN_ROWS)] for x in range(GRID_SIZE[0])]
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
            if das_timers[0] == 0 and drop_delay == 0:
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
            if das_timers[1] == 0 and drop_delay == 0:
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
            fall_timer -= (PUYO_FALL_TIME/2) - 1  # 2f fastfall

        # temporary reset board button
        if keys[pygame.K_r]:
            board_state = [[0 for y in range(GRID_SIZE[1] + HIDDEN_ROWS)] for x in range(GRID_SIZE[0])]

        if keys[pygame.K_z] and rotation_active[0]:
            rotate_logic(-1)
            rotation_active[0] = False
        elif not keys[pygame.K_z] and not rotation_active[0]:
            rotation_active[0] = True
        if keys[pygame.K_x] and rotation_active[1]:
            rotate_logic(1)
            rotation_active[1] = False
        elif not keys[pygame.K_x] and not rotation_active[1]:
            rotation_active[1] = True

        # ## LOGIC STUFF GOES HERE ## #
        if pop_delay > 1:
            pop_delay -= 1
        elif pop_delay == 1:
            pop_delay = 0
            perform_pop_puyos()
            if puyos_need_drop():
                drop_delay = DROP_TIMES[drop_step]
                drop_step += 1
        elif drop_delay > 0:
            drop_delay -= 1
        elif drop_step > 0:
            if puyos_need_drop():
                drop_delay = DROP_TIMES[drop_step]
                drop_step += 1
            else:
                if flag_pop_puyos() > 0:
                    pop_delay = TIME_TO_POP
                drop_delay = TIME_BETWEEN_PUYOS
                drop_step = 0
        else:
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
                # generate next puyo
                puyo_pos = [2, 1]
                cur_puyos = (random.randint(1, 4), random.randint(1, 4))
                rotation = 0
                if puyos_need_drop():
                    drop_delay = DROP_TIMES[drop_step]
                    drop_step += 1
                else:
                    if flag_pop_puyos() > 0:
                        pop_delay = TIME_TO_POP
                    drop_delay = TIME_BETWEEN_PUYOS
                    drop_step = 0

        # ## DRAW STUFF GOES HERE ## #

        screen.fill("black")
        # draw the grid
        square_size = math.floor((screen.get_height()*0.8)/GRID_SIZE[1])
        # thus,
        grid_pixelsize = (GRID_SIZE[0] * square_size, GRID_SIZE[1] * square_size)
        base_pos = ((screen.get_width() - grid_pixelsize[0])/2, (screen.get_height() - grid_pixelsize[1])/2)

        pop_highlight = int(((TIME_TO_POP - pop_delay) * 50) / TIME_TO_POP)
        # print(pop_highlight)
        for y in range(HIDDEN_ROWS, GRID_SIZE[1] + HIDDEN_ROWS):
            ypos = base_pos[1] + square_size * (y - HIDDEN_ROWS)
            for x in range(GRID_SIZE[0]):
                xpos = base_pos[0] + square_size * x
                fill = PUYO_COLORS[board_state[x][y]]
                if popping_board[x][y]:
                    fill = fill + pygame.Color(pop_highlight, pop_highlight, pop_highlight)
                if pop_delay == 0 and drop_delay == 0 and drop_step == 0:
                    if x == puyo_pos[0] and y == puyo_pos[1]:
                        fill = PUYO_COLORS[cur_puyos[0]]
                    elif x == other_puyo_pos()[0] and y == other_puyo_pos()[1]:
                        fill = PUYO_COLORS[cur_puyos[1]]
                pygame.draw.rect(screen, fill, pygame.Rect(xpos, ypos, square_size*0.9, square_size*0.9))

        pygame.display.flip()
        # print(board_state)
        dt = clock.tick(60) / 1000
    pygame.quit()
