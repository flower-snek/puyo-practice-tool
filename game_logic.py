import constants as CONST
import random
import pygame
import math


# oops all `self`s!


class board:
    def generate_puyo(self, restrict_color=-1):
        new_puyos = (random.randint(1, 4), random.randint(1, 4))
        if restrict_color != -1:
            puyo_1 = random.randint(1, 3)
            puyo_2 = random.randint(1, 3)
            if puyo_1 >= restrict_color:
                puyo_1 += 1
            if puyo_2 >= restrict_color:
                puyo_2 += 1
            new_puyos = (puyo_1, puyo_2)
        return new_puyos

    def __init__(self, settings, ghost_pattern=None):
        self.puyo_pos = [2, 0]
        self.pop_delay = 0
        self.drop_delay = 0
        self.drop_step = 0
        self.fall_time = CONST.PUYO_FALL_TIME / settings["fallmult"]
        self.fall_timer = self.fall_time
        self.das_timers = [0, 0]
        self.das_active = [False, False]
        self.rotation_active = [True, True]
        self.rotation = 0  # 0-3, up-right-down-left probably
        self.board_state = [[0 for y in range(CONST.GRID_SIZE[1] + CONST.HIDDEN_ROWS)] for x in range(CONST.GRID_SIZE[0])]
        self.popping_board = [[0 for y in range(CONST.GRID_SIZE[1] + CONST.HIDDEN_ROWS)] for x in range(CONST.GRID_SIZE[0])]
        self.mark_falling_squares = [[False for y in range(CONST.GRID_SIZE[1] + CONST.HIDDEN_ROWS)] for x in range(CONST.GRID_SIZE[0])]
        self.num_popped = 0
        self.finished = False

        self.latest_combo = 0
        self.max_combo = 0
        self.score = 0

        self.ghost_pattern = ghost_pattern

        self.puyo_graphics = CONST.PUYO_GRAPHICS_CB if settings["colorblind"] else CONST.PUYO_GRAPHICS

        # the first three pairs in a game consist of all but one color;
        # i think specifically they're supposed to include all 3 of the other colors
        # but... honestly i dont really feel like coding that right now so im just gonna make sure they have at MOST
        # 3 colors
        missing_color = random.randint(1, 4)
        self.cur_puyos = self.generate_puyo(missing_color)
        self.puyo_queue = [self.generate_puyo(missing_color), self.generate_puyo(missing_color)]

    def collision_logic(self):
        past_bottom = (self.puyo_pos[1] >= CONST.GRID_SIZE[1] + CONST.HIDDEN_ROWS) or (self.other_puyo_pos()[1] >= CONST.GRID_SIZE[1] + CONST.HIDDEN_ROWS)
        if past_bottom:
            return past_bottom
        overlapping = False
        if self.puyo_pos[1] >= 0:
            overlapping = overlapping or self.board_at(self.puyo_pos) != 0
        if self.other_puyo_pos()[1] >= 0:
            overlapping = overlapping or self.board_at(self.other_puyo_pos()) != 0

        return overlapping

    def board_at(self, pos):
        return self.board_state[pos[0]][pos[1]]

    def canMove(self, dx):
        within_bounds = 0 <= self.puyo_pos[0] + dx < CONST.GRID_SIZE[0] and 0 <= self.other_puyo_pos()[0] + dx < CONST.GRID_SIZE[0]
        if not within_bounds:
            return False
        space_available = True
        if self.puyo_pos[1] >= 0:
            space_available = space_available and self.board_at([self.puyo_pos[0] + dx, self.puyo_pos[1]]) == 0
        if self.other_puyo_pos()[1] >= 0:
            space_available = space_available and self.board_at([self.other_puyo_pos()[0] + dx, self.other_puyo_pos()[1]]) == 0
        return space_available

    def other_puyo_pos(self):
        o = [i for i in self.puyo_pos]
        if self.rotation == 0:
            o[1] -= 1
        elif self.rotation == 1:
            o[0] += 1
        elif self.rotation == 2:
            o[1] += 1
        elif self.rotation == 3:
            o[0] -= 1
        return o

    def rotate_logic(self, dir):
        # handles logic for rotations (mainly wall kicks, but also can't rotate once in a one wide well)
        # first do the rotation and pretend it's fine
        self.rotation = (self.rotation + dir) % 4
        # then check if it's fine
        # if the other puyo isn't in a wall right now, it's fine
        # print(other_puyo_pos()[1])
        if 0 <= self.other_puyo_pos()[0] < CONST.GRID_SIZE[0] and 0 <= self.other_puyo_pos()[1] < CONST.GRID_SIZE[
            1] + CONST.HIDDEN_ROWS and self.board_at(self.other_puyo_pos()) == 0:
            return
        # print("kicking (rotation =", rotation, ")")
        # if the rotation is 2 and we're colliding with something it must be something below, we can floor kick here
        if self.rotation == 2:
            self.puyo_pos[1] -= 1
            return
        # if the rotation is 1 or 3 then check the opposite direction; if it's clear, then move that way; otherwise, cancel the rotation
        if self.rotation == 1:
            if self.canMove(-1):
                self.puyo_pos[0] -= 1
            else:
                self.rotation = (self.rotation - dir) % 4
            return

        if self.rotation == 3:
            if self.canMove(1):
                self.puyo_pos[0] += 1
            else:
                self.rotation = (self.rotation - dir) % 4
            return

        # if somehow something else happens..... let's just cancel the rotation. be safe.
        self.rotation = (self.rotation - dir) % 4
        return

    def puyos_need_drop(self):
        dropped = False
        self.mark_falling_squares = [[False for y in range(CONST.GRID_SIZE[1] + CONST.HIDDEN_ROWS)] for x in range(CONST.GRID_SIZE[0])]
        for y in range(CONST.GRID_SIZE[1] + CONST.HIDDEN_ROWS - 2, -1, -1):
            for x in range(CONST.GRID_SIZE[0]):
                # if y == 0:
                # print(self.board_at([x, y]), self.board_at([x, y + 1]))
                if self.board_at([x, y]) != 0 and self.board_at([x, y + 1]) == 0:
                    # get that puyo down from there!!
                    self.board_state[x][y + 1] = self.board_state[x][y]
                    self.board_state[x][y] = 0
                    self.mark_falling_squares[x][y+1] = True
                    dropped = True
        return dropped

    def flag_pop_puyos(self):
        pop_count = 0
        for y in range(CONST.HIDDEN_ROWS, CONST.GRID_SIZE[1] + CONST.HIDDEN_ROWS):
            for x in range(CONST.GRID_SIZE[0]):
                if self.board_at([x, y]) != 0:
                    # this is probably really bad but i dont know a better way to do it and i dont exactly wanna copy code off the internet and its a small enough field that it works fine!!
                    current_group = self.board_at([x, y])
                    group_size = 1
                    checked_stack = [[x, y]]
                    check_stack = [[x + 1, y], [x - 1, y], [x, y + 1], [x, y - 1]]
                    while len(check_stack) > 0:
                        cur_check = check_stack.pop()
                        if 0 <= cur_check[0] < CONST.GRID_SIZE[0] and CONST.HIDDEN_ROWS <= cur_check[1] < CONST.GRID_SIZE[
                            1] + CONST.HIDDEN_ROWS:
                            if self.board_at(cur_check) == current_group:
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
                        self.popping_board[x][y] = group_size
                        pop_count += 1
        return pop_count

    def perform_pop_puyos(self):
        colors = []
        group_sizes = [0 for i in range(21)]  # im just assuming that no one's getting a 21+ clear in one color, theres probably a way to do this cleaner but for now i dont care
        PC = 0
        for y in range(CONST.HIDDEN_ROWS, CONST.GRID_SIZE[1] + CONST.HIDDEN_ROWS):
            for x in range(CONST.GRID_SIZE[0]):
                if self.popping_board[x][y] > 0:
                    if self.board_state[x][y] not in colors:
                        colors.append(self.board_state[x][y])
                    group_sizes[self.popping_board[x][y]] += 1/self.popping_board[x][y]
                    # i.e. if 5 puyos are in a group, each of them have self.popping_board[x][y] = 5, so giving each one a weight of 1/5 makes the final group_sizes value 1
                    self.board_state[x][y] = 0
                    self.popping_board[x][y] = 0
                    PC += 1
        # after this, the colors array should contain each color, and the group sizes array should contain the number of times each group appears in this clear
        # (i didnt expect trying to match the scoring system to take this much effort i didnt know how overly complex it was)
        # Score = (10 * PC) * (CP + CB + GB) where PC is the number of puyos popped,
        # CP is the combo power (determined by a table, copied into CONST.COMBO_POWER_TABLE),
        # CB is the color bonus (determined by a table, copied into CONST.COLOR_BONUS_TABLE),
        # GB is the group bonus (determined by a table, copied into CONST.GROUP_BONUS_TABLE),
        # and (CP + CB + GB) is at minimum 1 and at maximum 999 so its more like Score = (10 * PC) * MAX(1, MIN(999, CP + CB + GB))
        CP = CONST.COMBO_POWER_TABLE[self.latest_combo - 1]
        CB = CONST.COLOR_BONUS_TABLE[len(colors) - 1]
        GB = 0
        for i in range(4, len(group_sizes)):
            # print(i)
            GB += CONST.GROUP_BONUS_TABLE[min(i - 4, len(CONST.GROUP_BONUS_TABLE) - 1)] * group_sizes[i]
        score_gain = (10 * PC) * max(1, min(999, CP + CB + GB))
        self.score += score_gain
        # print(score_gain, self.score)

    def input(self, keys):
        for i in range(len(self.das_timers)):
            if self.das_timers[i] > 0:
                self.das_timers[i] -= 1
        if self.pop_delay == 0 and self.drop_delay == 0 and self.drop_step == 0:
            if keys[pygame.K_LEFT]:
                if self.das_timers[0] == 0 and self.drop_delay == 0:
                    if self.das_active[0]:
                        self.das_timers[0] = CONST.ARR
                    else:
                        self.das_timers[0] = CONST.DAS
                        self.das_active[0] = True
                    if self.canMove(-1):
                        self.puyo_pos[0] -= 1
            elif self.das_active[0]:
                self.das_active[0] = False
            if keys[pygame.K_RIGHT]:
                if self.das_timers[1] == 0 and self.drop_delay == 0:
                    if self.das_active[1]:
                        self.das_timers[1] = CONST.ARR
                    else:
                        self.das_timers[1] = CONST.DAS
                        self.das_active[1] = True
                    if self.canMove(1):
                        self.puyo_pos[0] += 1
            elif self.das_active[1]:
                self.das_active[1] = False
            if keys[pygame.K_DOWN]:
                if self.pop_delay == 0 and self.drop_delay == 0 and self.drop_step == 0:
                    self.fall_timer -= (self.fall_time / 2) - 1  # 2f fastfall

            if keys[pygame.K_z] and self.rotation_active[0]:
                self.rotate_logic(-1)
                self.rotation_active[0] = False
            elif not keys[pygame.K_z] and not self.rotation_active[0]:
                self.rotation_active[0] = True
            if keys[pygame.K_x] and self.rotation_active[1]:
                self.rotate_logic(1)
                self.rotation_active[1] = False
            elif not keys[pygame.K_x] and not self.rotation_active[1]:
                self.rotation_active[1] = True

        # temporary reset board button
        if keys[pygame.K_r]:
            self.board_state = [[0 for y in range(CONST.GRID_SIZE[1] + CONST.HIDDEN_ROWS)] for x in
                                range(CONST.GRID_SIZE[0])]
        # and temporary "fill in the ghost blocks" button
        if keys[pygame.K_y]:
            for y in range(CONST.GRID_SIZE[1] + CONST.HIDDEN_ROWS):
                for x in range(CONST.GRID_SIZE[0]):
                    if self.ghost_pattern is not None:
                        ghost_board_start_height = (CONST.GRID_SIZE[1] + CONST.HIDDEN_ROWS) - len(self.ghost_pattern)
                        if y - ghost_board_start_height >= 0:
                            if self.ghost_pattern[y - ghost_board_start_height][x]:
                                self.board_state[x][y] = self.ghost_pattern[y - ghost_board_start_height][x]

        if (self.finished and keys[pygame.K_RETURN]) or keys[pygame.K_ESCAPE]:
            return True
        return False

    def game_step(self):
        if not self.finished:
            if self.pop_delay > 1:
                self.pop_delay -= 1
            elif self.pop_delay == 1:
                self.pop_delay = 0
                self.perform_pop_puyos()
                if self.puyos_need_drop():
                    self.drop_delay = CONST.DROP_TIMES[self.drop_step]
                    self.drop_step += 1
            elif self.drop_delay > 0:
                self.drop_delay -= 1
            elif self.drop_step > 0:
                if self.puyos_need_drop():
                    self.drop_delay = CONST.DROP_TIMES[self.drop_step]
                    self.drop_step += 1
                else:
                    self.num_popped = self.flag_pop_puyos()
                    if self.num_popped > 0:
                        self.latest_combo += 1
                        if self.max_combo < self.latest_combo:
                            self.max_combo = self.latest_combo
                        self.pop_delay = CONST.TIME_TO_POP
                        # print(f"Combo: {self.latest_combo}")
                    self.drop_delay = CONST.TIME_BETWEEN_PUYOS
                    self.drop_step = 0
            else:
                self.fall_timer -= 1
                if self.fall_timer <= 0:
                    self.fall_timer = self.fall_time
                    self.puyo_pos[1] += 1

                if self.collision_logic():
                    self.latest_combo = 0
                    # print(puyo_pos)
                    # print(other_puyo_pos)
                    self.puyo_pos[1] -= 1
                    if self.puyo_pos[1] >= 0:
                        self.board_state[self.puyo_pos[0]][self.puyo_pos[1]] = self.cur_puyos[0]
                    if self.other_puyo_pos()[1] > 0:
                        self.board_state[self.other_puyo_pos()[0]][self.other_puyo_pos()[1]] = self.cur_puyos[1]
                    # generate next puyo
                    self.puyo_pos = [2, 0]

                    # self.cur_puyos = (random.randint(1, 4), random.randint(1, 4))
                    self.cur_puyos = self.puyo_queue[0]
                    self.puyo_queue[0] = self.puyo_queue[1]
                    self.puyo_queue[1] = self.generate_puyo()  # move along

                    self.rotation = 0
                    if self.puyos_need_drop():
                        self.drop_delay = CONST.DROP_TIMES[self.drop_step]
                        self.drop_step += 1
                    else:
                        self.num_popped = self.flag_pop_puyos()
                        if self.num_popped > 0:
                            self.latest_combo += 1
                            if self.max_combo < self.latest_combo:
                                self.max_combo = self.latest_combo
                            self.pop_delay = CONST.TIME_TO_POP
                            # print(f"Combo: {self.latest_combo}")
                        self.drop_delay = CONST.TIME_BETWEEN_PUYOS
                        self.drop_step = 0
                elif self.board_at([2, 1]) != 0:
                    self.game_over_logic()
                    # this should only activate if there are no clears to be made i hope

    def game_over_logic(self):
        # TODO: proper game over logic
        self.finished = True

    def draw_puyo_pair(self, x, y, rot, puyo_cols, size, screen):
        # given top left of puyo 0 (x, y), rotation, colors, and square size, draw 'em
        # fill = CONST.PUYO_COLORS[puyo_cols[0]]
        img = self.puyo_graphics[puyo_cols[0] - 1]
        img = pygame.transform.scale_by(img, math.floor(size / 16))
        # pygame.draw.rect(screen, fill, pygame.Rect(x, y, size - CONST.GRID_SPACING, size - CONST.GRID_SPACING))
        screen.blit(img, (x, y))
        # fill = CONST.PUYO_COLORS[puyo_cols[1]]
        img = self.puyo_graphics[puyo_cols[1] - 1]
        img = pygame.transform.scale_by(img, math.floor(size / 16))
        new_x = x
        new_y = y
        if rot == 0:
            new_y -= size
        elif rot == 1:
            new_x += size
        elif rot == 2:
            new_y += size
        elif rot == 3:
            new_x -= size
        # pygame.draw.rect(screen, fill, pygame.Rect(new_x, new_y, size - CONST.GRID_SPACING, size - CONST.GRID_SPACING))
        screen.blit(img, (new_x, new_y))

    def render(self, screen):
        # draw the grid
        square_size = 16 * math.floor((screen.get_height() * 0.9) / (CONST.GRID_SIZE[1] * 16)) + CONST.GRID_SPACING
        # print(square_size)
        # thus,
        grid_pixelsize = (CONST.GRID_SIZE[0] * square_size, CONST.GRID_SIZE[1] * square_size)
        base_pos = ((screen.get_width() - grid_pixelsize[0]) / 2, (screen.get_height() - grid_pixelsize[1]) / 2)

        pop_highlight = int(((CONST.TIME_TO_POP - self.pop_delay) * 50) / CONST.TIME_TO_POP) * 2
        # print(pop_highlight)
        for y in range(CONST.GRID_SIZE[1] + CONST.HIDDEN_ROWS):
            ypos = base_pos[1] + square_size * (y - CONST.HIDDEN_ROWS)
            for x in range(CONST.GRID_SIZE[0]):
                xpos = base_pos[0] + square_size * x
                '''
                fill = CONST.PUYO_COLORS[self.board_state[x][y]]
                if self.popping_board[x][y]:
                    fill = fill + pygame.Color(pop_highlight, pop_highlight, pop_highlight)
                '''
                '''
                if self.pop_delay == 0 and self.drop_delay == 0 and self.drop_step == 0:
                    if x == self.puyo_pos[0] and y == self.puyo_pos[1]:
                        fill = CONST.PUYO_COLORS[self.cur_puyos[0]]
                    elif x == self.other_puyo_pos()[0] and y == self.other_puyo_pos()[1]:
                        fill = CONST.PUYO_COLORS[self.cur_puyos[1]]
                '''
                if y >= CONST.HIDDEN_ROWS:
                    pygame.draw.rect(screen, CONST.PUYO_COLORS[0], pygame.Rect(xpos, ypos, square_size - CONST.GRID_SPACING, square_size - CONST.GRID_SPACING))
                else:
                    pygame.draw.rect(screen, CONST.PUYO_COLORS[0],
                                     pygame.Rect(xpos, ypos + ((square_size - CONST.GRID_SPACING) * (1 - CONST.HIDDEN_ROW_CROP)),
                                                 square_size - CONST.GRID_SPACING, (square_size - CONST.GRID_SPACING) * CONST.HIDDEN_ROW_CROP))
                # For the "ghost" board:
                if self.ghost_pattern is not None:
                    ghost_board_start_height = (CONST.GRID_SIZE[1] + CONST.HIDDEN_ROWS) - len(self.ghost_pattern)
                    # print(ghost_board_start_height)
                    if y - ghost_board_start_height >= 0:
                        if self.ghost_pattern[y - ghost_board_start_height][x]:  # why did i make this y x instead of x y
                            img = self.puyo_graphics[self.ghost_pattern[y - ghost_board_start_height][x] - 1].copy().convert_alpha()
                            img = pygame.transform.scale_by(img, math.floor(square_size / 16))
                            img.fill((255, 255, 255, 64), None, pygame.BLEND_RGBA_MULT)
                            crop = (0, 0, img.get_width(), img.get_height())
                            if y < CONST.HIDDEN_ROWS:
                                crop = (0, (1 - CONST.HIDDEN_ROW_CROP) * img.get_height(), img.get_width(),
                                        CONST.HIDDEN_ROW_CROP * img.get_height())
                            screen.blit(img, (xpos, ypos + crop[1]), crop)

                # For the actual board:
                if self.board_state[x][y] > 0:
                    img = self.puyo_graphics[self.board_state[x][y] - 1].copy().convert_alpha()
                    if self.popping_board[x][y]:
                        pixels = pygame.surfarray.pixels2d(img)
                        # print(pixels)
                        for px in range(img.get_width()):
                            for py in range(img.get_height()):
                                # print(int_to_argb(pixels[px, py]))
                                a, r, g, b = int_to_argb(pixels[px, py])
                                r = min(pop_highlight + r, 255)
                                g = min(pop_highlight + g, 255)
                                b = min(pop_highlight + b, 255)
                                pixels[px, py] = argb_to_int(a, r, g, b)
                        del pixels
                    img = pygame.transform.scale_by(img, math.floor(square_size / 16))
                    dropping_dy = 0
                    if self.mark_falling_squares[x][y]:
                        dropping_dy = square_size * (self.drop_delay / CONST.DROP_TIMES[self.drop_step - 1])
                    crop = (0, 0, img.get_width(), img.get_height())
                    if y < CONST.HIDDEN_ROWS:
                        crop = (0, (1 - CONST.HIDDEN_ROW_CROP) * img.get_height(), img.get_width(),
                                CONST.HIDDEN_ROW_CROP * img.get_height())
                    screen.blit(img, (xpos, ypos - dropping_dy + crop[1]), crop)

        if self.pop_delay == 0 and self.drop_delay == 0 and self.drop_step == 0:
            if not self.finished:
                remaining_drop_dist = self.fall_timer / self.fall_time
                self.draw_puyo_pair(base_pos[0] + square_size * self.puyo_pos[0],
                                    base_pos[1] + square_size * (self.puyo_pos[1] - CONST.HIDDEN_ROWS - remaining_drop_dist),
                                    self.rotation, self.cur_puyos, square_size, screen)
            # and draw the queue...
            queue_x_loc = base_pos[0] + grid_pixelsize[0] + square_size  # ahh! magic numbers! kill it!
            queue_y_loc = base_pos[1] + square_size
            self.draw_puyo_pair(queue_x_loc, queue_y_loc, 0, self.puyo_queue[0], square_size, screen)
            self.draw_puyo_pair(queue_x_loc, queue_y_loc + square_size * 3, 0, self.puyo_queue[1], square_size, screen)
        else:
            # because of when i trade off the puyos in the queue, i have to draw the current pair and the first in queue
            # rather than just the two in the queue. this is jank. dont be mad pls future me.
            queue_x_loc = base_pos[0] + grid_pixelsize[0] + square_size  # ahh! magic numbers! kill it! again!
            queue_y_loc = base_pos[1] + square_size
            self.draw_puyo_pair(queue_x_loc, queue_y_loc, 0, self.cur_puyos, square_size, screen)
            self.draw_puyo_pair(queue_x_loc, queue_y_loc + square_size * 3, 0, self.puyo_queue[0], square_size, screen)

        if self.latest_combo > 0:
            img = CONST.COMBO_GRAPHICS[self.latest_combo - 1]
            normal_size = img.get_rect()
            # slap this to the left of the board
            # also make it bigger immediately after a chain for dramatic effect
            scale = (1.5 - 0.5 * easeOutExpo(1 - (self.pop_delay / CONST.TIME_TO_POP))) * (1 + 1 * self.latest_combo / 19)  # max combo is 19 (mathematically)
            img = pygame.transform.scale_by(img, scale)
            size = img.get_rect()
            screen.blit(img, (base_pos[0] - normal_size.w - size.w/2, screen.get_height()/2 - size.h/2))

        # score
        score_txt = CONST.FONTS['s'].render(f'{min(self.score, 999999):0>6.0f} PTS', True, pygame.Color(255, 255, 255))
        size = score_txt.get_rect()
        screen.blit(score_txt, (screen.get_width()/2 - size.w / 2, base_pos[1] + grid_pixelsize[1] + size.h/2))

        if self.finished:
            text_surface = CONST.FONTS['l'].render("GAME OVER", True, pygame.Color(255, 255, 255))
            size = text_surface.get_rect()
            screen.blit(text_surface, (screen.get_width()/2 - size.w / 2, screen.get_height()/2 - size.h))
            text_surface = CONST.FONTS['m'].render(f"MAX COMBO: {self.max_combo}", True, pygame.Color(255, 255, 255))
            size = text_surface.get_rect()
            screen.blit(text_surface, (screen.get_width() / 2 - size.w / 2, screen.get_height()/2))


def int_to_argb(value):
    b = value % 256
    g = (value >> 8) % 256
    r = (value >> 16) % 256
    a = (value >> 24) % 256
    return a, r, g, b


def argb_to_int(a, r, g, b):
    return (a << 24) + (r << 16) + (g << 8) + b


def easeOutExpo(x):
    # adapted from https://easings.net/#easeOutExpo
    return 1 if x == 1 else 1 - math.pow(2, -10 * x)
