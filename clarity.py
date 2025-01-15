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

    core_address = "198.162.1.48"
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
        show_image("/home/evan/clarity/uwu.png")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Main process interrupted. Exiting.")
