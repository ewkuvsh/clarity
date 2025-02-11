import socket
from scapy.all import ARP, Ether, srp
import pickle
import select


def arp_for_ip(MAC, iface):
    broadcast = MAC
    arp_request = ARP(pdst="192.168.1.0/24")
    ether = Ether(dst=broadcast)
    packet = ether / arp_request

    answered, unanswered = srp(packet, timeout=2, iface=iface, verbose=False)

    for sent, received in answered:
        if received.hwsrc.lower() == target_mac.lower():
            print(received.psrc)
            return received.psrc

    return None


def establish_core_conn(server_ip, server_port):
    try:
        server_ip = "192.168.1.76"  # arp_for_ip(server_MAC, iface="wlan0") privilege issue i will solve later
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.settimeout(3)

        client_socket.connect((server_ip, server_port))
        print(f"Connected to {server_ip}:{server_port}")

        # response = client_socket.recv(1024)
        # print(f"Server response: {response.decode()}")
        client_socket.setblocking(False)
        print("successful conn")

        return client_socket

    except Exception as e:
        print(f"Error: {e}")


def establish_core_visual_conn(server_ip, server_port):
    try:
        server_ip = "192.168.1.76"  # arp_for_ip(server_MAC, iface="wlan0") privilege issue i will solve later
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.settimeout(1)
        client_socket.connect((server_ip, server_port))
        client_socket.settimeout(5)

        return client_socket

    except Exception as e:
        print(f"Error: {e}")


def send_data(client_socket, data):

    try:
        client_socket.sendall(data)
        # print("Data sent to server successfully.")
        return True
    except Exception as e:
        print(f"Error sending data: {e}")
        client_socket.close()
        return False


def receive_image(sock):
    try:
        length_bytes = sock.recv(4)
        if not length_bytes:
            raise ConnectionError("Socket closed before receiving data length.")

        data_length = int.from_bytes(length_bytes, "big")
        print(f"Expected data length: {data_length}")

        data = b""
        while len(data) < data_length:
            packet = sock.recv(4096)
            if not packet:
                raise ConnectionError("Socket connection closed while receiving data.")
            data += packet

        frame = pickle.loads(data)
        return frame
    except TimeoutError as timeout:
        return None
    except Exception as e:
        print(f"Error receiving data: {e}")
        if sock:
            try:
                sock.close()
                print("Socket closed due to error.")
            except Exception as close_error:
                print(f"Error closing socket: {close_error}")
        return None


def send_image(sock, frame):
    try:
        data = pickle.dumps(frame)

        sock.sendall(len(data).to_bytes(4, "big"))
        print(len(data))

        sock.sendall(data)

        return True
    except Exception as e:
        print(f"Error sending data: {e}")
        sock.close()
        return False


def receive_look(sock, timeout=1.0):

    try:
        ready_to_read, _, _ = select.select([sock], [], [], timeout)
        if ready_to_read:
            result = sock.recv(50).decode().split()
            return result
        else:
            return None
    except Exception as e:
        print(f"Error in receive_look: {e}")
        return None
