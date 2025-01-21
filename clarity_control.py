import serial
import select
import sys
import RPi.GPIO as GPIO
from scrounch_intelligence import voice_si
from clarity_comms import (
    establish_core_conn,
    send_image,
    establish_core_visual_conn,
    receive_look,
)
import multiprocessing
import pi_servo_hat
import time
import socket
import pickle
from picamera2 import Picamera2
from libcamera import Transform
import cv2


sock = None


def move_head(servos, xpos, ypos):
    servos.move_servo_position(0, ypos)
    servos.move_servo_position(1, xpos)


def onboard_face_track(words, servos, xpos, ypos):
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


def core_face_track(result, servos, xpos, ypos):
    print(result)
    x = int(result[0])
    y = int(result[1])
    if y > 120:  # or y < 110:
        ypos += 4
    elif y < 160:
        ypos -= 4

    if x > 320:
        xpos -= 4
    elif x < 360:
        xpos += 4

    move_head(servos, xpos, ypos)

    print("x coord is" + str(xpos))
    print("y coord is" + str(ypos))
    # if ypos > 80 or ypos < -180:
    # ypos = 0
    # if xpos > 160 or xpos < -160:
    # xpos = 0
    return xpos, ypos


def look(send_queue, core_address):
    global sock
    sock = establish_core_visual_conn(core_address, 5001)

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

    picam2 = Picamera2()
    picam2.configure(
        picam2.create_preview_configuration(
            main={"format": "RGB888", "size": (2304, 1296)},
            transform=Transform(rotation=180),
        )
    )
    picam2.start()

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
            print(sock == None)
            if time.time() % 30 < 1:
                periodic_action(core_address)

            line = ser.readline().decode("utf-8").strip()
            print(line)
            if line:
                words = line.split()
                xpos, ypos = onboard_face_track(words, servos, xpos, ypos)
                print(f"{xpos},{ypos}")
                last_seen = time.time()

            elif sock != None:
                try:
                    frame = picam2.capture_array()
                    frame = cv2.resize(frame, (640, 320), interpolation=cv2.INTER_AREA)
                    print("sending img")
                    send_image(sock, frame)
                    if sock != None:
                        result = receive_look(sock)
                        xpos, ypos = core_face_track(result, servos, xpos, ypos)
                        last_seen = time.time()

                    time.sleep(1)
                except Exception as e:
                    print(f"Error send/recv data: {e}")
                    sock.close()
                    sock = establish_core_visual_conn(core_address, 5001)

            # else:

            if time.time() - last_seen > 5:
                xpos = xpos - 2 * (xpos // abs(xpos)) if xpos != 0 else 0
                ypos = ypos - 2 * (ypos // abs(ypos)) if ypos != 0 else 0
                move_head(servos, xpos, ypos)


def periodic_action(core_address):
    global sock
    if sock == None:
        sock = establish_core_visual_conn(core_address, 5001)
