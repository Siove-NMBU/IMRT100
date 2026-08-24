import pygame
import os

# Initialize pygame mixer once
pygame.mixer.init()

PATH = "/home/student/Desktop/Link to RoboCode/IMRT100/python/raspi/soundfiles/horrible_drink.wav"

# Load the sound once
if os.path.exists(PATH):
    print("Sound file found:", PATH)
    sound = pygame.mixer.Sound(PATH)
else:
    print("ERROR: Sound file not found:", PATH)
    sound = None


def say_FAHHH():
    """Play the FAHHH sound."""
    
    if sound is not None:
        print("FAHHH!")
        sound.play()