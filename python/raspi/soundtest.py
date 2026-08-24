from playsound import playsound
# pip install playsound==1.2.2
import threading

path = "/home/pi/python/raspi/soundfiles/FAH.mp3" 

def play(path):
    playsound(path)


# t = threading.Thread(target=play, args=("C://Users//sindr//Music//Rnd Samples//terrible_drink_II.wav",))
t = threading.Thread(target=play, args=(path),)
t.start()
