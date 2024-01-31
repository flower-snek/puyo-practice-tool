import pygame
import math

GRID_SIZE = (6, 13)
GAME_SIZE = (1280, 720)

if __name__ == "__main__":
    pygame.init()
    running = True
    screen = pygame.display.set_mode(GAME_SIZE)
    clock = pygame.time.Clock()
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        # INPUT STUFF GOES HERE

        # DRAW STUFF GOES HERE
        screen.fill("black")
        # draw the grid
        square_size = math.floor((screen.get_height()*0.8)/GRID_SIZE[1])
        # thus,
        grid_pixelsize = (GRID_SIZE[0] * square_size, GRID_SIZE[1] * square_size)
        base_pos = ((screen.get_width() - grid_pixelsize[0])/2, (screen.get_height() - grid_pixelsize[1])/2)
        for y in range(GRID_SIZE[1]):
            ypos = base_pos[1] + square_size * y
            for x in range(GRID_SIZE[0]):
                xpos = base_pos[0] + square_size * x
                pygame.draw.rect(screen, pygame.Color(30, 30, 30), pygame.Rect(xpos, ypos, square_size*0.9, square_size*0.9))

        pygame.display.flip()
    pygame.quit()

