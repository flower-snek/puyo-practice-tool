import pygame
import constants as CONST
import game_logic as game
import os
import csv
import math

'''
TODO LIST:
- ~~the practice mode that this was made for~~ MOSTLY DONE?
- ~~settings menu~~ MOSTLY DONE?
- ~~colorblind friendly~~ DONE
- ~~puyo graphics~~ DONE mostly
- ~~combo count~~ DONE
- ~~smoother puyo falling~~ DONE
- ~~pause button~~ actually im just making this an exit button oh well gonna throw it in the controls display ig
- ~~actual game over screen~~ ACTUALLY MAYBE I WON'T UNLESS I HAVE A GOOD IDEA FOR IT
- ~~display controls~~ (just a title screen graphic?) JUST A TITLE SCREEN GRAPHIC
- background
- ~~title screen improvements~~ THE LOGO IS ENOUGH I GUESS
- ~~scoring~~ DONE
- remove debug controls -- maybe i only do this on the official submitted version, then keep the debug controls for the presentation
'''


class Screen:  # enum thing bc otherwise it would just be numbers
    MAIN_MENU = 1
    GAMEPLAY = 2
    PATTERN_DECIDE = 3
    SETTINGS = 4


COLORBLIND_TOGGLE = False
FALL_SPEED_SEL = 0


def draw_button(scr, text, font, tcol, x, y, w, h, bcol):
    pygame.draw.rect(scr, bcol, pygame.Rect(x, y, w, h))
    text_surface = font.render(text, True, tcol)
    size = text_surface.get_rect()
    scr.blit(text_surface, (x + w/2 - size.w/2, y + h/2 - size.h/2))


def mm_render(scr, opt):
    # print(opt)
    # just draw some buttons ig with a highlight on the selected one
    draw_button(scr, "FREE PLAY", CONST.FONTS['m'], pygame.Color(255, 255, 255), scr.get_width()/3, scr.get_height()/2 - 50, scr.get_width()/3, 50,
                pygame.Color((90, 50, 50) if opt == 0 else (50, 20, 20)))

    draw_button(scr, "PRACTICE", CONST.FONTS['m'], pygame.Color(255, 255, 255), scr.get_width()/3, scr.get_height()/2 + 40, scr.get_width()/3, 50,
                pygame.Color((50, 50, 90) if opt == 1 else (20, 20, 50)))

    draw_button(scr, "OPTIONS", CONST.FONTS['m'], pygame.Color(255, 255, 255), scr.get_width()/3, scr.get_height() / 2 + 130, scr.get_width() / 3, 50,
                pygame.Color((50, 90, 50) if opt == 2 else (20, 50, 20)))

    # oh also the tile screen now
    size = CONST.TITLE_GRAPHIC.get_rect()
    scr.blit(CONST.TITLE_GRAPHIC, (scr.get_width()/2 - size.w/2, scr.get_height()/5 - size.h/2))

    size = CONST.CONTROLS_GRAPHIC.get_rect()
    scr.blit(CONST.CONTROLS_GRAPHIC, (scr.get_width() / 2 - size.w / 2, scr.get_height() - size.h * 1.1))


def pat_render(scr, opt, pattern):
    draw_button(scr, "BACK", CONST.FONTS['m'], pygame.Color(255, 255, 255), scr.get_width()/3, scr.get_height()/2 - 130, scr.get_width()/3, 50,
                pygame.Color((90, 50, 50) if opt == 0 else (50, 20, 20)))

    # i dug a hole for myself by pre-defining the position and the fact that theres only one text per button.
    # so its time for another jank solution: the button is actually two buttons, one for each text box
    draw_button(scr, f"<- {pattern[0]} ->", CONST.FONTS['m'], pygame.Color(255, 255, 255), scr.get_width()/4, scr.get_height()/2 - 40, scr.get_width()/2, 40,
                pygame.Color((50, 50, 90)))
    draw_button(scr, pattern[1], CONST.FONTS['xs'], pygame.Color(255, 255, 255), scr.get_width() / 4, scr.get_height() / 2, scr.get_width() / 2, 40,
                pygame.Color((50, 50, 90)))

    draw_button(scr, "START", CONST.FONTS['m'], pygame.Color(255, 255, 255), scr.get_width()/3, scr.get_height() / 2 + 80, scr.get_width() / 3, 50,
                pygame.Color((50, 90, 50) if opt == 1 else (20, 50, 20)))


def set_render(scr, opt):
    draw_button(scr, f"COLORBLIND COLORS: {'YES' if COLORBLIND_TOGGLE else 'NO'}", CONST.FONTS['m'], pygame.Color(255, 255, 255), scr.get_width() / 3,
                scr.get_height() / 2 - 115, scr.get_width() / 3, 50,
                pygame.Color((50, 50, 50) if opt == 0 else (20, 20, 20)))

    draw_button(scr, f"FALL SPEED: {CONST.FALL_SPEED_MULTS[FALL_SPEED_SEL]}x", CONST.FONTS['m'], pygame.Color(255, 255, 255), scr.get_width() / 3,
                scr.get_height() / 2 - 25, scr.get_width() / 3, 50,
                pygame.Color((50, 50, 50) if opt == 1 else (20, 20, 20)))

    draw_button(scr, "BACK", CONST.FONTS['m'], pygame.Color(255, 255, 255), scr.get_width() / 3,
                scr.get_height() / 2 + 65, scr.get_width() / 3, 50,
                pygame.Color((90, 50, 50) if opt == 2 else (50, 20, 20)))


def draw_background(scr):
    scr.fill("black")
    # uh uh uh when in doubt grid
    # rotation = 15 * math.sin(pygame.time.get_ticks() / 7000) nvm rotation is really expensive
    bg_surface = pygame.Surface((scr.get_width() + scr.get_height(), scr.get_width() + scr.get_height()))
    bg_size = bg_surface.get_rect()
    bg_square_no = 15
    bg_square_size = bg_size.w / bg_square_no
    bg_square_indent = 0.05
    offset = (pygame.time.get_ticks() / 200) % bg_square_size
    bonus_indent_offset = pygame.time.get_ticks() / 1500
    for x in range(bg_square_no):
        xpos = x * bg_square_size
        for y in range(bg_square_no):
            ypos = y * bg_square_size
            this_indent = bg_square_indent + max(2 * math.sin(bonus_indent_offset + (xpos + 2*ypos) / (5 * bg_square_size)) - 1, 0) * 2 * bg_square_indent # jank
            # print(this_indent)
            pygame.draw.rect(bg_surface, pygame.Color(20, 20, 20), pygame.Rect(offset + xpos + bg_square_size * this_indent,
                                                                               1.4 * offset + ypos + bg_square_size * this_indent,
                                                                               bg_square_size * (1 - 2 * this_indent),
                                                                               bg_square_size * (1 - 2 * this_indent)))
    scr.blit(bg_surface, (scr.get_width()/2 - bg_size.w/2, scr.get_height()/2 - bg_size.h/2))


def get_patterns():
    pattern_files = os.listdir("patterns")
    pattern_arrays = []
    for f in pattern_files:
        if f.endswith(".csv"):
            # print(f)
            csv_file = open(f"patterns/{f}", 'r', newline='')
            csv_reader = csv.reader(csv_file, delimiter=' ')
            pattern_array = []
            desc = ""
            for row in csv_reader:
                # print(row)
                # first row is the description while the other rows are the pattern (in number form); i want the pattern
                # rows to be integers while keeping the description alone, but i have no index variable here so
                # i instead do this kinda jank setup
                if row[0].isdigit():
                    numeric_row = [int(i) for i in row]
                    # print(numeric_row)
                    pattern_array.append(numeric_row)
                else:
                    desc = row[0]
            csv_file.close()
            pattern_arrays.append([f, desc, pattern_array])
    return pattern_arrays


def settings_array():
    return {"fallmult": CONST.FALL_SPEED_MULTS[FALL_SPEED_SEL],
            "colorblind": COLORBLIND_TOGGLE}


if __name__ == "__main__":
    pygame.init()

    running = True
    screen = pygame.display.set_mode(CONST.GAME_SIZE)
    clock = pygame.time.Clock()

    cur_screen = Screen.MAIN_MENU

    # main menu variables
    mm_option = 0
    mm_num_buttons = 3  # this is a const im just lazy

    # practice menu variables
    p_selection = 0

    patterns = get_patterns()
    # print(patterns[0])

    # gameplay variable (the board one)
    board = None

    while running:

        # ## INPUT STUFF GOES HERE ## #

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if cur_screen == Screen.MAIN_MENU:
                # print(event.type)
                if event.type == pygame.KEYDOWN:

                    if event.key == pygame.K_DOWN:
                        mm_option += 1
                    elif event.key == pygame.K_UP:
                        mm_option -= 1
                    mm_option = mm_option % mm_num_buttons

                    if event.key == pygame.K_RETURN:
                        # print(mm_option)
                        if mm_option == 0:
                            board = game.board(settings_array())
                            cur_screen = Screen.GAMEPLAY
                        if mm_option == 1:
                            cur_screen = Screen.PATTERN_DECIDE
                            mm_option = 0
                        if mm_option == 2:
                            cur_screen = Screen.SETTINGS
                            mm_option = 0

            elif cur_screen == Screen.PATTERN_DECIDE:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_DOWN:  # hard coding woo
                        mm_option += 1
                    elif event.key == pygame.K_UP:
                        mm_option -= 1
                    mm_option = mm_option % 2

                    if event.key == pygame.K_LEFT:
                        p_selection -= 1
                    elif event.key == pygame.K_RIGHT:
                        p_selection += 1
                    p_selection = p_selection % len(patterns)

                    if event.key == pygame.K_RETURN:
                        if mm_option == 0:
                            cur_screen = Screen.MAIN_MENU
                        if mm_option == 1:
                            board = game.board(settings_array(), ghost_pattern=patterns[p_selection][2])
                            cur_screen = Screen.GAMEPLAY
                            mm_option = 0

            elif cur_screen == Screen.SETTINGS:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_DOWN:
                        mm_option += 1
                    elif event.key == pygame.K_UP:
                        mm_option -= 1
                    mm_option = mm_option % 3
                    if mm_option == 0:
                        if event.key == pygame.K_LEFT or event.key == pygame.K_RIGHT:
                            COLORBLIND_TOGGLE = not COLORBLIND_TOGGLE
                    if mm_option == 1:
                        if event.key == pygame.K_LEFT:
                            FALL_SPEED_SEL -= 1
                        elif event.key == pygame.K_RIGHT:
                            FALL_SPEED_SEL += 1
                    FALL_SPEED_SEL = FALL_SPEED_SEL % len(CONST.FALL_SPEED_MULTS)

                    if event.key == pygame.K_RETURN:
                        # might as well make these also toggle/change values
                        if mm_option == 0:
                            COLORBLIND_TOGGLE = not COLORBLIND_TOGGLE
                        if mm_option == 1:
                            FALL_SPEED_SEL = (FALL_SPEED_SEL + 1) % len(CONST.FALL_SPEED_MULTS)
                        if mm_option == 2:
                            cur_screen = Screen.MAIN_MENU
                            mm_option = 0

        keys = pygame.key.get_pressed()

        if cur_screen == Screen.GAMEPLAY:
            if board.input(keys):
                cur_screen = Screen.MAIN_MENU

        # ## LOGIC STUFF GOES HERE ## #

        if cur_screen == Screen.GAMEPLAY:
            board.game_step()

        # ## DRAW STUFF GOES HERE ## #

        draw_background(screen)
        if cur_screen == Screen.MAIN_MENU:
            mm_render(screen, mm_option)
        if cur_screen == Screen.GAMEPLAY:
            board.render(screen)
        if cur_screen == Screen.PATTERN_DECIDE:
            pat_render(screen, mm_option, patterns[p_selection])
        if cur_screen == Screen.SETTINGS:
            set_render(screen, mm_option)

        pygame.display.flip()
        # print(board_state)
        clock.tick(60)
    pygame.quit()
