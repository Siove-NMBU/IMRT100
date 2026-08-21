# Example code for IMRT100 robot project
# H var her 

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
TURNING_SPEED = 50
STOP_DISTANCE = 18 #25


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


def turn_robot_random_angle(direction, duration):

    direction = random.choice([-1, 1])
    iterations = random.randint(10, 25)

    for i in range(iterations):
        motor_serial.send_command(TURNING_SPEED * direction, -TURNING_SPEED * direction)
        time.sleep(0.10)

def turn_robot_right(direction, duration):

    direction = RIGHT
    iterations = int(duration * 10)

    for i in range(iterations):
        motor_serial.send_command(TURNING_SPEED * direction, -TURNING_SPEED * direction)
        time.sleep(0.10)

def turn_robot_left(direction, duration):

    direction = LEFT
    iterations = int(duration * 10)

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


# Et fortapt forsøk på å få roboten til å justere seg i henhold til om det er en forbanna vegg foran den eller ikke

    # Roboten vil snu seg når sensoren foran slår ut mest (da kjører den direkte på en vegg)
    if dist_front < dist_left and dist_right:

        turn_robot_right(RIGHT, 0.1)

    # Hvis venstre sensor kommer nær en vegg vil den justere seg til høyre helt til
    # sensoren ikke slår ut lenger
    elif dist_left < STOP_DISTANCE:
        drive_robot(RIGHT, 0.06)

    # Samme gjelder her
    elif dist_right < STOP_DISTANCE:
        drive_robot(LEFT, 0.06)    

    # Hvis det er ingenting foran sensorene, vil den kjøre rett fram
    else:
        drive_robot(FORWARDS, 0.1)

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
        # If there is nothing in front of the robot it continues driving forwards
        drive_robot(FORWARDS, 0.1)"""




    DEFAULT_SPEED = 100  # DRIVING_SPEED
    TARGET_DISTANCE_RIGHT = 20
    TARGET_DISTANCE_FRONT = 20 # this was at 50
    OFFSET_FACTOR_R = 2 * DEFAULT_SPEED * (DEFAULT_SPEED // TARGET_DISTANCE_RIGHT)
    OFFSET_FACTOR_F = 2 * DEFAULT_SPEED * (DEFAULT_SPEED // TARGET_DISTANCE_FRONT)

    motor_speed_left = DEFAULT_SPEED + OFFSET_FACTOR_F * (min(0, dist_front - TARGET_DISTANCE_FRONT))
    motor_speed_right = DEFAULT_SPEED - OFFSET_FACTOR_R * (dist_right - TARGET_DISTANCE_RIGHT)

    motor_serial.send_command(motor_speed_left, motor_speed_right)  # Left - Right motors

#    print("D_L(1):", dist_left, " D_C(3):", dist_front, " D_R(2):", dist_right,
#          f'MSL: {motor_speed_left} MSR: {motor_speed_right}')
    print("Dist_left:", dist_left, " Dist_front:", dist_front, " Dist_right:", dist_right, f'MSL: {motor_speed_left} MSR: {motor_speed_right}')

    # ## LOOP END ## #

# motor_serial has told us that its time to exit
# we have now exited the loop
# It's only polite to say goodbye
print("Goodbye")
