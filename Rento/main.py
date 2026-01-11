import pygame
import random
import time
import sys
import math
import numpy
from pygame import mixer
from collections import deque

# Initialize pygame
pygame.init()
mixer.init(frequency=22050, size=-16, channels=2, buffer=512)

# Screen dimensions
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Mindless Meditation")

# Colors
BG_COLOR = (240, 240, 235)
CIRCLE_COLORS = [
    (173, 216, 230),  # Light blue
    (144, 238, 144),  # Light green
    (255, 182, 193),  # Light pink
    (221, 160, 221),  # Light purple
    (255, 228, 181),  # Light orange
]

# Circle properties
min_radius = 20
max_radius = 60
circle_lifetime = 3  # seconds
spawn_interval = 1.5  # seconds

# Game variables
score = 0
font = pygame.font.SysFont('Arial', 32)
small_font = pygame.font.SysFont('Arial', 24)
clock = pygame.time.Clock()
running = True

# Reaction time tracking
reaction_times = deque(maxlen=100)  # Stores last 100 reaction times
current_circle_appear_time = 0


# Sound generation functions
def generate_bell_sound(freq=440, duration=0.5):
    sample_rate = mixer.get_init()[0]
    samples = int(duration * sample_rate)
    buffer = numpy.zeros((samples, 2), dtype=numpy.int16)

    for i in range(samples):
        t = float(i) / sample_rate
        # Bell-like envelope
        envelope = math.exp(-5 * t)
        # Sine wave with slight frequency modulation
        wave = math.sin(2 * math.pi * freq * t * (1 + 0.1 * math.sin(2 * math.pi * 2 * t)))
        value = int(32767 * envelope * wave)
        buffer[i][0] = value  # Left channel
        buffer[i][1] = value  # Right channel

    sound = pygame.sndarray.make_sound(buffer)
    sound.set_volume(0.3)
    return sound


def generate_ambience():
    sample_rate = mixer.get_init()[0]
    samples = sample_rate * 10  # 10 seconds (will loop)
    buffer = numpy.zeros((samples, 2), dtype=numpy.int16)

    for i in range(samples):
        t = float(i) / sample_rate
        # Low frequency noise with gentle waves
        value = int(8000 * (math.sin(0.3 * t) + 0.3 * math.sin(5.3 * t) + 0.1 * math.sin(23 * t)))
        buffer[i][0] = value  # Left channel
        buffer[i][1] = value  # Right channel

    sound = pygame.sndarray.make_sound(buffer)
    sound.set_volume(0.1)
    return sound


# Generate sounds
try:
    click_sounds = [
        generate_bell_sound(440),
        generate_bell_sound(523.25),  # C note
        generate_bell_sound(659.25)  # E note
    ]
    background_sound = generate_ambience()
    background_sound.play(-1)  # Loop background sound
except Exception as e:
    print(f"Sound generation failed: {e}. Continuing without sound.")
    click_sounds = []
    background_sound = None


class Circle:
    def __init__(self):
        global current_circle_appear_time
        self.radius = random.randint(min_radius, max_radius)
        self.x = random.randint(self.radius, WIDTH - self.radius)
        self.y = random.randint(self.radius, HEIGHT - self.radius)
        self.color = random.choice(CIRCLE_COLORS)
        self.created_time = time.time()
        current_circle_appear_time = self.created_time
        self.clicked = False

    def draw(self):
        if not self.clicked:
            pygame.draw.circle(screen, self.color, (self.x, self.y), self.radius)
            # Draw a subtle inner circle for depth
            pygame.draw.circle(screen, (255, 255, 255), (self.x, self.y), self.radius - 5, 2)

    def is_expired(self):
        return time.time() - self.created_time > circle_lifetime and not self.clicked

    def contains_point(self, point):
        distance = ((self.x - point[0]) ** 2 + (self.y - point[1]) ** 2) ** 0.5
        return distance <= self.radius


circles = []
last_spawn_time = time.time()


def spawn_circle():
    circles.append(Circle())


def draw_score():
    score_text = font.render(f"Score: {score}", True, (100, 100, 100))
    screen.blit(score_text, (20, 20))

    # Display average reaction time if we have data
    if reaction_times:
        avg_reaction = sum(reaction_times) / len(reaction_times)
        reaction_text = small_font.render(f"Avg Reaction: {avg_reaction * 1000:.0f} ms", True, (100, 100, 100))
        screen.blit(reaction_text, (20, 60))
    else:
        reaction_text = small_font.render("Avg Reaction: -", True, (100, 100, 100))
        screen.blit(reaction_text, (20, 60))


def draw_instructions():
    instructions = font.render("Click the circles to meditate", True, (150, 150, 150))
    screen.blit(instructions, (WIDTH // 2 - instructions.get_width() // 2, HEIGHT - 50))


# Main game loop
while running:
    current_time = time.time()

    # Spawn new circles at intervals
    if current_time - last_spawn_time > spawn_interval:
        spawn_circle()
        last_spawn_time = current_time

    # Handle events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            for circle in circles:
                if not circle.clicked and circle.contains_point(event.pos):
                    circle.clicked = True
                    score += 1
                    # Calculate reaction time (current time - circle appear time)
                    reaction_time = time.time() - circle.created_time
                    reaction_times.append(reaction_time)
                    if click_sounds:
                        random.choice(click_sounds).play()
                    break

    # Clear screen
    screen.fill(BG_COLOR)

    # Draw and update circles
    for circle in circles[:]:
        circle.draw()
        if circle.is_expired():
            circles.remove(circle)

    # Draw UI elements
    draw_score()
    draw_instructions()

    # Update display
    pygame.display.flip()
    clock.tick(60)

# Clean up
pygame.quit()
sys.exit()