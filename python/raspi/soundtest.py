import pygame
import time
import os


pygame.mixer.init()

path = "/home/student/Desktop/Link to RoboCode/IMRT100/python/raspi/soundfiles/FAH.wav"

print("File exists:", os.path.exists(path))

if os.path.exists(path):
    print("Playing:", path)
    
    # Load and play the sound
    sound = pygame.mixer.Sound(path)
    sound.play()
    
    # Keep the script running while the sound plays
    while pygame.mixer.get_busy():
        time.sleep(0.1)
        
    print("Finished")
else:
    print("Error: File path is incorrect.")


