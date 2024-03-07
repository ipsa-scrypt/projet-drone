import pygame

# Initialize Pygame
pygame.init()

# Set up the display
width, height = 800, 600
screen = pygame.display.set_mode((width, height))
pygame.display.set_caption("Pygame Example")
clock = pygame.time.Clock()
running = True

while running:

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
            print("Espace DOWN")

        elif event.type == pygame.KEYUP and event.key == pygame.K_SPACE:
            print("Espace UP")

    # Add a clock to control the frame rate
    clock.tick(60)
    # Add code to update the display
    pygame.display.flip()


pygame.quit()
