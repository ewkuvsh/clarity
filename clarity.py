import serial
import sys
import RPi.GPIO as GPIO
from scrounch_intelligence import voice_si
from clarity_control import look
from screen import show_text, show_image
import multiprocessing
from multiprocessing import Value, Process, Queue
import clarity_IPC
from clarity_comms import send_audio_data, establish_core_conn


import pi_servo_hat
import time


if __name__ == "__main__":
    sock = establish_core_conn("192.168.1.48", 5000)
    core_connected = Value("b", False)
    voice_send_queue = Queue()
    look_send_queue = Queue()
    recv_queue = Queue()  # non-voice will have a shared send queue

    process_look = multiprocessing.Process(
        target=look,
        args=(
            core_connected,
            recv_queue,
            look_send_queue,
        ),
        daemon=True,
    )
    process_voice = multiprocessing.Process(
        target=voice_si,
        args=(core_connected, recv_queue, voice_send_queue),
        daemon=True,
    )

    # Start the processes

    process_look.start()
    process_voice.start()

    try:
        # Keep the main process running to prevent child processes from exiting
        # show_image("/home/evan/clarity/uwu.png")
        while True:
            send_audio_data(sock, recv_queue.get())
            try:
                voice_send_queue.put(sock.recv(4096).decode("utf-8"))
            except BlockingIOError:
                continue

    except KeyboardInterrupt:
        print("Main process interrupted. Exiting.")


# idea, spawned processes has a send queue and a recv queue.

# if sock is not None:
#     if send_audio_data(sock, data) == False:
#         sock = None
#         return False, ""

#    try:
#        user_input = sock.recv(4096)

#        if user_input == b"":
#           return False, ""

#      return True, user_input.decode("utf-8")  # Decode if needed

#  except (BlockingIOError, OSError):
#     return False, ""
