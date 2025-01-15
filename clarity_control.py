import serial
import sys
import RPi.GPIO as GPIO
from scrounch_intelligence import voice_si
from screen import show_text, show_image
import multiprocessing
import clarity_IPC

import pi_servo_hat
import time


def move_head(servos, xpos, ypos):
    servos.move_servo_position(0, ypos)
    servos.move_servo_position(1, xpos)


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

        move_head(servos, xpos, ypos)

        #        print("x coord is" + str(x))
        #       print("y coord is" + str(y))
        if ypos > 80 or ypos < -180:
            ypos = 0
        if xpos > 160 or xpos < -160:
            xpos = 0
    return xpos, ypos


def look(core_connected, send_queue, recv_queue):

    last_seen = 0
    ypos = 0
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
                last_seen = time.time()
            if time.time() - last_seen > 5:
                xpos = xpos - 2 * (xpos // abs(xpos)) if xpos != 0 else 0
                ypos = ypos - 2 * (ypos // abs(ypos)) if ypos != 0 else 0
                move_head(servos, xpos, ypos)
