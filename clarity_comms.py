import socket
import clarity_IPC


def establish_core_conn(server_ip, server_port):
    try:
        # Create a socket object
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # Connect to the server
        client_socket.connect((server_ip, server_port))
        print(f"Connected to {server_ip}:{server_port}")

        # Send a message to the server
        client_socket.sendall(b"Hello, server! This is the client.")

        # Receive response from the server
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


if __name__ == "__main__":
    # Server IP and port (replace with the actual IP and port)
    server_ip = "192.168.1.3"  # The IP address of the server
    server_port = 5000  # The port the server is listening on
    sock = establish_core_conn(server_ip, server_port)


def recv_message(sock):
    # Read the first 4 bytes to get the message length
    raw_length = sock.recv(4)
    if not raw_length:
        raise ConnectionError("Socket connection closed")
    length = int.from_bytes(raw_length, "big")

    # Read the actual data
    return recv_all(sock, length)
