import serial
import sys
import RPi.GPIO as GPIO
from scrounch_intelligence import voice_si
from screen import show_text, show_image
from clarity_control import look
import multiprocessing
from multiprocessing import Queue
import pi_servo_hat
import time

if __name__ == "__main__":

    core_address = "8c:1d:96:bb:3d:e9"

    recv_queue = Queue()

    process_look = multiprocessing.Process(
        target=look,
        args=(
            recv_queue,
            core_address,
        ),
        daemon=True,
    )

    process_voice = multiprocessing.Process(
        target=voice_si,
        args=(
            recv_queue,
            core_address,
        ),
        daemon=True,
    )

    # Start the processes
    process_look.start()
    process_voice.start()

    try:
        # Keep the main process running to prevent child processes from exiting
        show_image("/home/evan/clarity/happy.png")
        while True:
            if not recv_queue.empty():

                new_face = recv_queue.get()

                if new_face == "uwu":
                    show_image("/home/evan/clarity/uwu.png")
                elif new_face == "confused":
                    show_image("/home/evan/clarity/confused.png")
                elif new_face == "happy":
                    show_image("/home/evan/clarity/happy.png")

    except KeyboardInterrupt:
        print("Main process interrupted. Exiting.")
