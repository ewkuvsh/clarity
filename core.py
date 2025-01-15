import socket
import vosk
import json
import clarity_IPC

model = vosk.Model("vosk-model-en-us-0.42-gigaspeech")
recognizer = vosk.KaldiRecognizer(model, 44100)


def enable_keep_alive(client_socket):
    client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
    client_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPIDLE, 1)
    client_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPINTVL, 3)
    client_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPCNT, 2)


def start_core(host, port):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, port))
    server_socket.listen()
    print(f"Server listening on {host}:{port}...")

    while True:
        try:
            client_socket, client_address = server_socket.accept()
            print(f"Connection established with {client_address}")
            enable_keep_alive(client_socket)

            client_socket.sendall(b"Connection successful!\n")

            try:
                print("Receiving audio data...")
                while True:
                    data = client_socket.recv(15000)  # Adjust buffer size as needed
                    # print(f"Processing {len(data)} bytes of audio data.")
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


if __name__ == "__main__":
    # Start the server
    sock = start_core(socket.gethostbyname(socket.gethostname()), 5000)
