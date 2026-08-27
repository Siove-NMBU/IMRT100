# Example code for IMRT100 robot project


# Import some modules that we need
import imrt_robot_serial
import signal
import time
import sys
import random
import numpy as np
from playsound import playsound
import pygame
from math import exp, copysign


LEFT = -1
RIGHT = 1
FORWARDS = 1
BACKWARDS = -1
DRIVING_SPEED = 100
TURNING_SPEED = 100
STOP_DISTANCE = 25


def stop_robot(duration):

    iterations = int(duration * 10)

    for i in range(iterations):
        motor_serial.send_command(0, 0)
        time.sleep(0.10)


def drive_robot(direction, duration):

    speed = DRIVING_SPEED * direction   # Direction is -1 or 1
    iterations = int(duration * 10)

    for i in range(iterations):
        motor_serial.send_command(speed, speed)
        time.sleep(0.10)


def turn_robot_random_angle():

    direction = random.choice([-1, 1])
    iterations = random.randint(10, 25)

    for i in range(iterations):
        motor_serial.send_command(TURNING_SPEED * direction, -TURNING_SPEED * direction)
        time.sleep(0.10)


# We want our program to send commands at 10 Hz (10 commands per second)
execution_frequency = 10  # Hz
execution_period = 1. / execution_frequency  # seconds


# Create motor serial object
motor_serial = imrt_robot_serial.IMRTRobotSerial()


# Open serial port. Exit if serial port cannot be opened
try:
    motor_serial.connect("/dev/ttyACM0")
except Exception as e:
    print(f'Could not open port, {e}. Is your robot connected?\nExiting program')
    sys.exit()


# Start serial receive thread
motor_serial.run()

sound_objects = []
list_sounds = ["/home/student/Desktop/Link to RoboCode/IMRT100/python/raspi/soundfiles/aoe2-no.wav",
                "/home/student/Desktop/Link to RoboCode/IMRT100/python/raspi/soundfiles/FAH.wav",
                "/home/student/Desktop/Link to RoboCode/IMRT100/python/raspi/soundfiles/horrible_drink.wav",
                "/home/student/Desktop/Link to RoboCode/IMRT100/python/raspi/soundfiles/WINDOWS_XP_ERROR.wav",
                "/home/student/Desktop/Link to RoboCode/IMRT100/python/raspi/soundfiles/ERRORSOUND.wav"]

pygame.mixer.init(frequency=44100)   # init once at program start

for soundpaths in list_sounds:
    sound_objects.append(pygame.mixer.Sound(soundpaths))  # preload into RAM

# Boot sound
boot_sound = pygame.mixer.Sound(
    "/home/student/Desktop/Link to RoboCode/IMRT100/python/raspi/soundfiles/bring-it-on-seige.wav"
)
if not pygame.mixer.get_busy():
    boot_sound.play()

# # SYSTEM CONSTANTS # #
DEFAULT_SPEED = 160  # DRIVING_SPEED -- DEFAULT WAS 160 -- 200 WORKS EVEN BETTER
TARGET_DISTANCE_LEFT = 60  # DEFAULT WAS 60
TARGET_DISTANCE_RIGHT = 60  # DEFAULT WAS 60
TARGET_DISTANCE_FRONT = 15  # DEFAULT WAS 15
MAX_DIST = 255
DRIFT_BIAS = 0.25  # DEFAULT WAS 0.2 -- 0.25 SEEMS TO WORK BETTER
DIFF_SCALE = 0.5
E_POW = 1.5  # 1.5
T_TURN = 1
SPIN_SPEED = 120

prev_dist_front = 0
prev_dist_right = 0
prev_dist_left = 0

print("Entering loop. Ctrl+c to terminate")
while not motor_serial.shutdown_now:

    # ## LOOP START ## #

    # Makes it so a random sound (from a list) plays every time the rear sensor activates
    i = random.randint(1, len(sound_objects))
    sound = sound_objects[i - 1]

    # Get and print readings from distance sensors
    dist_left = motor_serial.get_dist_1()
    dist_right = motor_serial.get_dist_2()
    dist_front = motor_serial.get_dist_3()
    dist_rear = motor_serial.get_dist_4()

    # Try to limit spikes in sensor readings
    MAX_DIST_DELTA = 20
    delta_dist_left = dist_left - prev_dist_left
    if abs(delta_dist_left) > MAX_DIST_DELTA:
        sound_objects[4].play()
        # dist_left = prev_dist_left + copysign(MAX_DIST_DELTA, delta_dist_left)
    """
    delta_dist_right = dist_right - prev_dist_right
    if abs(delta_dist_right) > MAX_DIST_DELTA:
        dist_right = prev_dist_right + copysign(MAX_DIST_DELTA, delta_dist_right)

    delta_dist_front = dist_front - prev_dist_front
    if abs(delta_dist_front) > MAX_DIST_DELTA:
        dist_front = prev_dist_front + copysign(MAX_DIST_DELTA, delta_dist_front)
    """

    # Play sound when rear sensor is close
    if dist_rear < 20:
        if not pygame.mixer.get_busy():
            sound_objects[0].play()

    diff = 0
    dTR = dist_right - TARGET_DISTANCE_RIGHT
    dTL = dist_left - TARGET_DISTANCE_LEFT
    dTF = dist_front - TARGET_DISTANCE_FRONT

    # If too close to obstacle in front, turn away for a bit
    if dist_front < TARGET_DISTANCE_FRONT:
        crnt_t = time.time()
        while dist_rear > TARGET_DISTANCE_FRONT and (time.time() - crnt_t) < T_TURN:
            motor_serial.send_command(-SPIN_SPEED, SPIN_SPEED)
            dist_rear = motor_serial.get_dist_4()
            print("Spinning to winning:", round(time.time() - crnt_t, 2), f'Rear: {dist_rear}')
            sound_objects[1].play()
        continue

    # Calculate motor mix differentials for the iteration
    diff += 0 if (dTL > 0) else -int(abs(dTL)**E_POW)
    # diff += round(-DRIFT_BIAS * dist_right) if (dTR > 0) else int(abs(dTR)**E_POW)

    sig_steepness = 0.05
    sig_midpoint = 40
    sig_max = 200
    # -(sig_max + 5) // (1 + exp(-sig_steepness * (dTR - sig_midpoint))) - 20
    # diff += round(-DRIFT_BIAS * dist_right)  # Krenging til høyre

    # Motor mix
    motor_mix_left = DEFAULT_SPEED - round(DIFF_SCALE * diff)
    motor_mix_right = DEFAULT_SPEED + round(DIFF_SCALE * diff)

    print("D_L(1):", dist_left, " D_C(3):", dist_front, " D_R(2):", dist_right, " D_B(4):", dist_rear,
          f'MSL: {motor_mix_left} MSR: {motor_mix_right}\n',
          f'dTL: {dTL} dTF: {dTF} dTR: {dTR}, scld diff: {DIFF_SCALE * diff}')

    motor_serial.send_command(int(round(motor_mix_left)), int(round(motor_mix_right)))  # Left - Right motors

    prev_dist_front = dist_front
    prev_dist_right = dist_right
    prev_dist_left = dist_left

    # ## LOOP END ## #

# It's only polite to say goodbye
print("Goodbye")
