import RPi.GPIO as GPIO
import time

BUZZ_PIN = 23
DUTY = 10

# BCM pin naming
GPIO.setmode(GPIO.BCM)

# Turn off GPIO warnings
GPIO.setwarnings(False)

# Set buzzer pin to output
GPIO.setup(BUZZ_PIN, GPIO.OUT)

p = GPIO.PWM(BUZZ_PIN, 250) # channel=12 frequency=50Hz
p.start(0)

# Test
p.ChangeDutyCycle(DUTY)
p.ChangeFrequency(440)
time.sleep(3)
p.ChangeDutyCycle(0)
time.sleep(1)

GPIO.cleanup()
print("Goodbye")
p.stop()