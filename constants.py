import pygame
# sigh

# constants
GRID_SIZE = (6, 12)  # THE BOARD IS 12 HIGH????? IVE HAD IT AT 13 THIS WHOLE TIME BECAUSE A SOURCE SAID IT WAS BUT THAT INCLUDED THE GHOST ROW
HIDDEN_ROWS = 1
HIDDEN_ROW_CROP = 0.25
GAME_SIZE = (1280, 720)
PUYO_COLORS = [pygame.Color(30, 30, 30), pygame.Color(80, 40, 40), pygame.Color(80, 80, 40), pygame.Color(40, 80, 40), pygame.Color(40, 40, 80)]


# frame data (src: https://puyonexus.com/wiki/Puyo_Puyo_Tsu/Frame_Data_Tables)
PUYO_FALL_TIME = 16
DAS = 8  # Delayed Auto Shift
ARR = 2  # Auto Repeat Rate
DROP_TIMES = [10, 5, 4, 3, 3, 3, 3, 2, 2, 2, 2, 2, 2, 2, 2]  # i added an extra 2 just in case tbh
TIME_BETWEEN_PUYOS = 16

# scoring constants (src: https://puyonexus.com/wiki/Scoring)
COMBO_POWER_TABLE = [0, 8, 16, 32, 64, 96, 128, 160, 192, 224, 256, 288, 320, 352, 384, 416, 448, 480, 512, 544, 576, 608, 640, 672]  # for 1 chain, 2 chain, etc etc
COLOR_BONUS_TABLE = [0, 3, 6, 12, 24]  # for 1 - 5 colors
GROUP_BONUS_TABLE = [0, 2, 3, 4, 5, 6, 7, 10]  # this looks like a pain to calculate how i'm doing it. for 4, 5, 6, 7, 8, 9, 10, 11+ groups

TIME_TO_POP = 48  # long animation...
GROUP_TO_POP = 4  # 4 is default ofc, but other numbers can be ""fun""

GRID_SPACING = 0

# graphics
PUYO_GRAPHICS = [pygame.image.load(f"graphics/puyo{i}.png") for i in range(4)]
PUYO_GRAPHICS_CB = [pygame.image.load(f"graphics/puyocb{i}.png") for i in range(4)]
COMBO_GRAPHICS = [pygame.image.load(f"graphics/combo{i + 1}.png") for i in range(19)]
TITLE_GRAPHIC = pygame.image.load("graphics/logo.png")
CONTROLS_GRAPHIC = pygame.image.load("graphics/controls.png")

pygame.font.init()
SYSFONT = pygame.font.get_default_font()
FONTS = {
    "xs": pygame.font.SysFont(SYSFONT, 24),
    "s": pygame.font.SysFont(SYSFONT, 30),
    "m": pygame.font.SysFont(SYSFONT, 36),
    "l": pygame.font.SysFont(SYSFONT, 72),
}

# setting options
FALL_SPEED_MULTS = [1.0, 1.5, 2.0, 4.0, 8.0, 0.1, 0.2, 0.5]