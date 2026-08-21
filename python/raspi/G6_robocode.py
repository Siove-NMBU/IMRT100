# Example code for IMRT100 robot project


# Import some modules that we need
import imrt_robot_serial
import signal
import time
import sys
import random

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

# Now we will enter a loop that will keep looping until the program terminates
# The motor_serial object will inform us when it's time to exit the program
# (say if the program is terminated by the user)
print("Entering loop. Ctrl+c to terminate")
while not motor_serial.shutdown_now:

    # ## LOOP START ## #

    # Get and print readings from distance sensors
    dist_left = motor_serial.get_dist_1()
    dist_right = motor_serial.get_dist_2()
    dist_front = motor_serial.get_dist_3()

    """# Check if there is an obstacle in the way
    if dist_left < STOP_DISTANCE or dist_right < STOP_DISTANCE:
        # There is an obstacle in front of the robot
        # First let's stop the robot for 1 second
        print("Obstacle!")
        stop_robot(1)

        # Reverse for 0.5 second
        drive_robot(BACKWARDS, 0.5)

        # Turn random angle
        turn_robot_random_angle()

    else:
        # If there is nothing in front of the robot it continus driving forwards
        drive_robot(FORWARDS, 0.1)"""

    """
    # Hugging the right wall until maze completion
    # DEFAULT_SPEED = DRIVING_SPEED
    # TARGET_DISTANCE_RIGHT = 30
    if dist_right > TARGET_DISTANCE_RIGHT:
        turn rightwards
    else:
        turn leftwards
    """
    DEFAULT_SPEED = 180  # DRIVING_SPEED
    TARGET_DISTANCE_LEFT = 30
    TARGET_DISTANCE_RIGHT = 30
    TARGET_DISTANCE_FRONT = 30
    MAX_DIST = 255
    DRIFT_BIAS = 0.15
    DIFF_SCALE = 0.6

    diff = 0
    dTR = dist_right - TARGET_DISTANCE_RIGHT
    dTL = dist_left - TARGET_DISTANCE_LEFT
    dTF = dist_front - TARGET_DISTANCE_FRONT

    """
    PSEUDOCODE
    Motor input: Default speed +- differential
    Differential 0 -> Default speed forward. Differential 100 -> Right is 100 more than left

    Motor mix: Distance readings from sensors contribute to final differential.
        Left side:  Differential -= (min(dist_left - TARGET_DIDTANCE_LEFT), 0)^2
        Right side: Differential += (min(dist_right - TARGET_DIDTANCE_RIGHT), 0)^2
    """
    diff += 0 if (dTL > 0) else -(dist_left - TARGET_DISTANCE_LEFT)**2
    diff += round(-DRIFT_BIAS * dist_right) if (dTR > 0) else (dist_right - TARGET_DISTANCE_RIGHT)**2
    #diff += 0 if dist_front > TARGET_DISTANCE_FRONT else 1 // (abs(dTL - dTR) + 1) * (dTF**2) // 2

    # Motor mix
    motor_mix_left = DEFAULT_SPEED - round(DIFF_SCALE * diff)  # - (MAX_DIST // (dist_front + 1))
    motor_mix_right = DEFAULT_SPEED + round(DIFF_SCALE * diff)  # - (MAX_DIST // (dist_front + 1))

    motor_serial.send_command(motor_mix_left, motor_mix_right)  # Left - Right motors

    print("D_L(1):", dist_left, " D_C(3):", dist_front, " D_R(2):", dist_right,
          f'MSL: {motor_mix_left} MSR: {motor_mix_right}')

    # ## LOOP END ## #

# motor_serial has told us that its time to exit
# we have now exited the loop
# It's only polite to say goodbye
print("Goodbye")
