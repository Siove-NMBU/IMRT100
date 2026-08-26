import sys
import time
import random as rnd

import imrt_robot_serial
import imrt_xbox

import pygame


# ---------- Innstillinger ----------
SERIAL_PORT = "/dev/ttyACM0"
LOOP_HZ = 20

# Forsiktige startverdier. Test før dere eventuelt øker dem.
SPEED_PRECISION = 160
SPEED_NORMAL = 280
SPEED_RACE = 400
MAX_COMMAND = 400

TURN_GAIN = 0.85
EXPO = 0.35
DEADZONE = 0.12

# Endre fortegn dersom roboten kjører eller svinger feil vei.
FORWARD_SIGN = 1
TURN_SIGN = 1
MOTOR_1_SIGN = 1
MOTOR_2_SIGN = 1

# Antatt fysisk sensorrekkefølge. Må kontrolleres på deres robot.
SENSOR_FRONT = 1
SENSOR_FRONT_LEFT = 2
SENSOR_FRONT_RIGHT = 3
SENSOR_REAR = 4

# Vernet starter av til sensorrekkefølgen er kontrollert.
SENSOR_GUARD_DEFAULT = False

# Startverdier i centimeter.
FRONT_STOP_CM = 18
FRONT_SLOW_CM = 45
REAR_STOP_CM = 15
REAR_SLOW_CM = 35
NO_ECHO_CM = 255

soundpath = "/home/student/Desktop/Link to RoboCode/IMRT100/python/raspi/soundfiles/Roar.wav"

pygame.mixer.init(frequency=44100)
sound = pygame.mixer.Sound(soundpath)

aoe_death_sounds = []
death_sounds_path = ["/home/student/Desktop/Link to RoboCode/IMRT100/python/raspi/soundfiles/aoe2_death1.wav",
                     "/home/student/Desktop/Link to RoboCode/IMRT100/python/raspi/soundfiles/aoe2_death2.wav",
                     "/home/student/Desktop/Link to RoboCode/IMRT100/python/raspi/soundfiles/aoe2_death3.wav",
                     "/home/student/Desktop/Link to RoboCode/IMRT100/python/raspi/soundfiles/aoe2_death4.wav",
                     "/home/student/Desktop/Link to RoboCode/IMRT100/python/raspi/soundfiles/aoe2_death6.wav"]

for soundpath in death_sounds_path:
    aoe_death_sounds.append(pygame.mixer.Sound(soundpath))  # preload into RAM


def clamp(value, minimum, maximum):
    return max(minimum, min(maximum, value))


def shape_axis(value):
    """Mykere respons nær midten av spaken."""
    value = clamp(float(value), -1.0, 1.0)
    return (1.0 - EXPO) * value + EXPO * value**3


def just_pressed(current, previous):
    return bool(current) and not bool(previous)


def read_buttons(controller):
    return {
        "A": controller.get_a(),
        "B": controller.get_b(),
        "X": controller.get_x(),
        "Y": controller.get_y(),
        "LB": controller.get_left_bumper(),
        "RB": controller.get_right_bumper(),
        "L_trig": controller.get_left_trigger(),
        "R_trig": controller.get_right_trigger()
    }


def read_sensors(robot):
    raw = {
        1: robot.get_dist_1(),
        2: robot.get_dist_2(),
        3: robot.get_dist_3(),
        4: robot.get_dist_4(),
    }
    named = {
        "front": raw[SENSOR_FRONT],
        "front_left": raw[SENSOR_FRONT_LEFT],
        "front_right": raw[SENSOR_FRONT_RIGHT],
        "rear": raw[SENSOR_REAR],
    }
    return named


def speed_scale(distance, stop_distance, slow_distance):
    """Lag gradvis nedbremsing mellom slow_distance og stop_distance."""
    distance = float(distance)

    if distance <= 0 or distance >= NO_ECHO_CM:
        return 1.0
    if distance <= stop_distance:
        return 0.0
    if distance >= slow_distance:
        return 1.0

    return (distance - stop_distance) / (slow_distance - stop_distance)


def apply_sensor_guard(throttle, sensors, enabled):
    """
    Frontsensoren begrenser fremoverkjøring.
    Baksensoren begrenser rygging.
    Diagonalsensorene logges, men overstyrer ikke manuell kjøring ennå.
    """
    if not enabled:
        return throttle, ""

    if throttle > 0:
        scale = speed_scale(
            sensors["front"], FRONT_STOP_CM, FRONT_SLOW_CM
        )
        throttle *= scale
        if scale == 0:
            return throttle, "STOPP FORAN"
        if scale < 1:
            return throttle, "Bremser foran"

    elif throttle < 0:
        scale = speed_scale(
            sensors["rear"], REAR_STOP_CM, REAR_SLOW_CM
        )
        throttle *= scale
        if scale == 0:
            return throttle, "STOPP BAK"
        if scale < 1:
            return throttle, "Bremser bak"

    return throttle, ""


def motor_mix(throttle, turn):
    """Bland fremoverfart og sving til to motorverdier."""
    motor_1 = throttle + TURN_GAIN * turn
    motor_2 = throttle - TURN_GAIN * turn

    largest = max(1.0, abs(motor_1), abs(motor_2))
    return motor_1 / largest, motor_2 / largest


def main():
    controller = imrt_xbox.IMRTxbox(deadzone=DEADZONE)
    robot = imrt_robot_serial.IMRTRobotSerial()

    try:
        robot.connect(SERIAL_PORT)
    except Exception as error:
        print(f"Kunne ikke åpne {SERIAL_PORT}: {error}")
        print("Kontroller USB-kabelen mellom Raspberry Pi og Arduino.")
        controller.shutdown(blocking=False)
        sys.exit(1)

    robot.run()

    armed = True  # False
    mode = "NORMAL"
    speed_limit = SPEED_NORMAL
    guard_enabled = SENSOR_GUARD_DEFAULT

    previous = read_buttons(controller)
    loop_period = 1.0 / LOOP_HZ
    last_status = 0.0

    print("\nXbox-kontroller:")
    print("  Venstre spak opp/ned = fremover/bakover")
    print("  Høyre spak sideveis = sving")
    print("  A = start/normal, X = presisjon, Y = rask")
    print("  B = nødstopp, LB = sensorvern på/av")
    print("  Ctrl+C = avslutt")
    print("  Antatt sensororden: D1=front, D2=front-venstre,")
    print("                       D3=front-høyre, D4=bak\n")

    try:
        while not robot.shutdown_now:
            start_time = time.monotonic()
            buttons = read_buttons(controller)

            # Play roar
            if just_pressed(buttons["Y"], previous["Y"]):
                print("button pressed")
                if not pygame.mixer.get_busy():
                    sound.play()

            elif just_pressed(buttons["X"], previous["X"]):
                armed = True
                mode = "PRESISJON"
                speed_limit = SPEED_PRECISION

            elif just_pressed(buttons["A"], previous["A"]):
                armed = True
                mode = "NORMAL"
                speed_limit = SPEED_NORMAL

            elif just_pressed(buttons["B"], previous["B"]):
                armed = True
                mode = "RASK"
                speed_limit = SPEED_RACE

            if just_pressed(buttons["L_trig"], previous["L_trig"]):
                print("Left trigger pressed")
                if not pygame.mixer.get_busy():
                    aoe_death_sounds[rnd.randint(0, len(aoe_death_sounds) - 1)].play()

            if just_pressed(buttons["LB"], previous["LB"]):
                guard_enabled = not guard_enabled
                print("\nSensorvern:", "PÅ" if guard_enabled else "AV")

            throttle = FORWARD_SIGN * shape_axis(controller.get_left_y())
            turn = TURN_SIGN * shape_axis(controller.get_right_y())

            sensors = read_sensors(robot)
            warning = ""

            if not armed:
                command_1 = 0
                command_2 = 0
            else:
                throttle, warning = apply_sensor_guard(
                    throttle, sensors, guard_enabled
                )
                motor_1, motor_2 = motor_mix(throttle, turn)

                command_1 = int(clamp(
                    round(motor_1 * speed_limit) * MOTOR_1_SIGN,
                    -MAX_COMMAND,
                    MAX_COMMAND,
                ))
                command_2 = int(clamp(
                    round(motor_2 * speed_limit) * MOTOR_2_SIGN,
                    -MAX_COMMAND,
                    MAX_COMMAND,
                ))

            robot.send_command(command_1, command_2)

            now = time.monotonic()
            if now - last_status >= 0.5:
                print(
                    f"\r{mode:<9} | M1={command_1:>4} M2={command_2:>4} "
                    f"| F={sensors['front']:>3} "
                    f"FL={sensors['front_left']:>3} "
                    f"FR={sensors['front_right']:>3} "
                    f"BAK={sensors['rear']:>3} cm "
                    f"| Vern={'PÅ' if guard_enabled else 'AV':<2} "
                    f"| {warning:<14}",
                    end="",
                    flush=True,
                )
                last_status = now

            previous = buttons

            elapsed = time.monotonic() - start_time
            if elapsed < loop_period:
                time.sleep(loop_period - elapsed)

    finally:
        print("\nStopper roboten ...")

        for _ in range(5):
            try:
                robot.send_command(0, 0)
            except Exception:
                break
            time.sleep(0.05)

        try:
            robot._shutdown()
        except Exception:
            pass

        controller.shutdown()
        print("Programmet er avsluttet.")


if __name__ == "__main__":
    main()