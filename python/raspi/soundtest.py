from playsound import playsound
import os

# path = "/home/pi/python/raspi/soundfiles/FAH.mp3"
path = "/home/student/Desktop/Link to RoboCode/IMRT100/python/raspi/soundfiles/FAH.wav"


print("File exists:", os.path.exists(path))
print("Playing:", path)

playsound(path)

print("Finished")

