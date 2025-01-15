import socket


def establish_core_conn(server_ip, server_port):
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.settimeout(3)

        client_socket.connect((server_ip, server_port))
        print(f"Connected to {server_ip}:{server_port}")

        client_socket.sendall(b"Hello, server! This is the client.")

        response = client_socket.recv(1024)
        print(f"Server response: {response.decode()}")
        client_socket.setblocking(False)

        return client_socket

    except Exception as e:
        print(f"Error: {e}")


def send_audio_data(client_socket, data):

    try:
        client_socket.sendall(data)
        # print("Data sent to server successfully.")
        return True
    except Exception as e:
        print(f"Error sending data: {e}")
        client_socket.close()
        return False
