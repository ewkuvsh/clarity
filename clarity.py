import serial
import sys
import RPi.GPIO as GPIO
from scrounch_intelligence import voice_si
from screen import show_text, show_image
import multiprocessing

import pi_servo_hat
import time


def face_track(words, servos, xpos, ypos):
    if words[0] == "Face":

        x = int(words[2][2:-1])
        y = int(words[3][2:-1])
        if y > 120:  # or y < 110:
            ypos += 2
        elif y < 110:
            ypos -= 2

        if x > 140:
            xpos -= 2
        elif x < 110:
            xpos += 2

        servos.move_servo_position(0, ypos)

        servos.move_servo_position(1, xpos)

        print("x coord is" + str(x))
        print("y coord is" + str(y))
        if ypos > 80 or ypos < -180:
            ypos = -40
        if xpos > 160 or xpos < -160:
            xpos = 0
    return xpos, ypos


def look():

    ypos = -70
    xpos = 10
    baud_rate = 115200

    x_servo = 1
    y_servo = 0

    left_front_leg = 2
    left_back_leg = 3
    right_front_leg = 4
    right_back_leg = 5

    servos = pi_servo_hat.PiServoHat()
    servos.restart()
    serial_port = "/dev/ttyACM0"
    print(servos.get_servo_position(1))
    print(servos.get_servo_position(0))
    servos.move_servo_position(0, ypos)
    servos.move_servo_position(1, xpos)

    servos.move_servo_position(2, 0)
    servos.move_servo_position(3, 0)
    servos.move_servo_position(4, 0)
    servos.move_servo_position(5, 0)

    with serial.Serial(serial_port, baud_rate, timeout=1) as ser:
        print("listening")

        while True:
            line = ser.readline().decode("utf-8").strip()
            if line:
                words = line.split()
                xpos, ypos = face_track(words, servos, xpos, ypos)
                print(xpos)
                print(ypos)


# def main():

# await asyncio.gather(look(), scrounch_intelligence.voice_si())


if __name__ == "__main__":

    process_look = multiprocessing.Process(target=look, daemon=True)
    process_voice = multiprocessing.Process(target=voice_si, daemon=True)

    # Start the processes
    process_look.start()
    process_voice.start()

    try:
        # Keep the main process running to prevent child processes from exiting
        show_image("uwu.png")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Main process interrupted. Exiting.")
