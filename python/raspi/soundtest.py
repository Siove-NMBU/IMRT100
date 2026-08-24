from playsound import playsound
# pip install playsound==1.2.2
import threading


def play(path):
    playsound(path)


t = threading.Thread(target=play, args=("C://Users//sindr//Music//Rnd Samples//terrible_drink_II.wav",))
t.start()
