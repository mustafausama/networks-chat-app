import socket

def is_port_available(hostname, port, udp=False):
    try:
        # Attempt to create a socket and bind to the specified port
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) if not udp else socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.bind((hostname, port))
            return True  # Port is available
    except:
        return False  # Port is not available


def find_available_port(hostname, start_port = 0, end_port = 65535, udp=False):
    for port in range(start_port, end_port):
        if is_port_available(hostname, port, udp):
            return port


def sendTCPMessage(tcpClientSocket, message):
    tcpClientSocket.send(message.encode())


def receiveTCPMessage(tcpClientSocket):
    message = tcpClientSocket.recv(1024).decode()
    return message


def get_input(msg=""):
    if msg: print(msg, end="")
    return input()


def get_hostname():
    hostname=socket.gethostname()
    try:
        res = socket.gethostbyname(hostname)
    except socket.gaierror:
        raise ValueError("Hostname %s could not be resolved" % hostname)
    return res


def generate_random_secret():
    import random
    import string
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
