import socket
import select
import vosk
import json
import numpy as np
import pickle
from clarity_comms import receive_image
import cv2
from facenet_pytorch import MTCNN
import torch
import multiprocessing
import time

model = vosk.Model("vosk-model-en-us-0.42-gigaspeech")
recognizer = vosk.KaldiRecognizer(model, 44100)
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

mtcnn = MTCNN(keep_all=True, device=device)


def enable_keep_alive(client_socket):
    client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
    client_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPIDLE, 1)
    client_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPINTVL, 3)
    client_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPCNT, 2)


def start_core_audio(host, port):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, port))
    server_socket.listen()
    print(f"Server listening on {host}:{port}...")

    while True:
        try:
            client_socket, client_address = server_socket.accept()
            print(f"Connection established with {client_address}")

            try:
                print("Receiving audio data...")
                while True:
                    data = client_socket.recv(15000)
                    print(f"Processing {len(data)} bytes of audio data.")
                    if recognizer.AcceptWaveform(data):
                        result = recognizer.Result()
                        user_input = json.loads(result)["text"]
                        print(user_input)
                        client_socket.sendall(user_input.encode("utf-8"))

                    if not data:  # If no data, client has disconnected
                        print(f"Connection closed by client {client_address}")
                        break
            except Exception as e:
                print(f"Error receiving data: {e}")
            finally:
                client_socket.close()
                print(f"Connection with {client_address} closed.")

        except Exception as e:
            print(f"Error with client connection: {e}")

    server_socket.close()


def process_image(frame):
    boxes, probs, landmarks = mtcnn.detect(frame, landmarks=True)

    if landmarks is not None:
        print(landmarks[0][2])
        return True, f"{int(landmarks[0][2][0])} {int(landmarks[0][2][1])}"

    else:
        return False, None


def start_core_visual(host, port):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, port))
    enable_keep_alive(server_socket)

    server_socket.listen()
    print(f"Server listening on {host}:{port}...")
    while True:
        try:
            client_socket, client_address = server_socket.accept()
            print(f"Connection established with {client_address}")
            enable_keep_alive(client_socket)

            try:
                print("Receiving video data...")
                while True:
                    ready_to_read, _, _ = select.select([client_socket], [], [], 1.0)
                    if ready_to_read:
                        frame = receive_image(client_socket)
                        if frame is None:
                            print(f"Connection closed by client {client_address}")
                            break
                        face, result = process_image(frame)
                        if face:
                            client_socket.sendall(result.encode())
                        print(f"Received image of shape: {frame.shape}")
                    else:
                        print("No data available to read.")

            except Exception as e:
                print(f"Error receiving data: {e}")
            finally:
                client_socket.close()
                print(f"Connection with {client_address} closed.")

        except Exception as e:
            print(f"Error with client connection: {e}")

    server_socket.close()


# Start the server
# start_server("0.0.0.0", 8000)


if __name__ == "__main__":
    # Start the server

    process_core_look = multiprocessing.Process(
        target=start_core_visual,
        args=(socket.gethostbyname(socket.gethostname()), 5001),
        daemon=True,
    )

    process_core_voice = multiprocessing.Process(
        target=start_core_audio,
        args=(socket.gethostbyname(socket.gethostname()), 5000),
        daemon=True,
    )
    process_core_voice.start()

    # process_core_look.start()

    start_core_visual(socket.gethostbyname(socket.gethostname()), 5001)
