import socket

def find_available_port(hostname, start_port, end_port):
    for port in range(start_port, end_port):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            s.bind((hostname, port))
            s.close()
            return port
        except socket.error as e:
            if e.errno == 98:  # errno 98 means Address already in use
                continue
            else:
                raise
