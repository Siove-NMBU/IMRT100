from playsound import playsound
import os

path = "/home/pi/python/raspi/soundfiles/FAH.mp3"

print("File exists:", os.path.exists(path))
print("Playing:", path)

playsound(path)

print("Finished")

