import socket, select, logging
from .client_thread import ClientThread
from chat.common.utils import find_available_port
from chat.common.exceptions import RoomAlreadyExistsException

def handle_new_TCP_connection(tcp_socket: socket.SocketType, server_context):
    tcpClientSocket, addr = tcp_socket.accept()
    newThread = ClientThread(addr[0], addr[1], tcpClientSocket, server_context)
    newThread.start()

def handle_UDP_message(udp_socket: socket.SocketType, server_context):
    message, clientAddress = udp_socket.recvfrom(1024)
    message = message.decode().split()
    # print("Received from " + clientAddress[0] + ":" + str(clientAddress[1]) + " -> " + " ".join(message))
    if message[0] == "HELLO":
        # checks if the account that this hello message 
        # is sent from is online
        username = message[1]
        ip, port = message[2].split(":")
        # if username in server_context.tcpThreads and (ip, int(port)) in server_context.onlinePeers:
        if username in server_context.tcpThreads and server_context.tcpThreads[username].ip == ip and server_context.tcpThreads[username].port == int(port):
            server_context.tcpThreads[username].resetTimeout()
            print("Adding " + username + " to online peers with address " + str(clientAddress) + "...")
            server_context.tcpThreads[username].peerUdpAddress = clientAddress
            # print("=== Hello is received from " + username)
            # logging.info("Received from " + clientAddress[0] + ":" + str(clientAddress[1]) + " -> " + " ".join(message))

class ServerContext:
    PORT_BASE = 15500
    def __init__(self) -> None:
        hostname = socket.gethostname()
        try:
            self.host = socket.gethostbyname(hostname)
        except socket.gaierror:
            raise ValueError("Hostname %s could not be resolved" % hostname)


        self.tcp_port = find_available_port(self.host, ServerContext.PORT_BASE+100, ServerContext.PORT_BASE+200)
        self.udp_port = find_available_port(self.host, ServerContext.PORT_BASE, ServerContext.PORT_BASE+100)
        
        # self.onlinePeers = {}
        self.tcpThreads = {}

        self.chatRooms = {}
        
        self.tcpSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.tcpSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.udpSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udpSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        self.tcpSocket.bind((self.host, self.tcp_port))
        self.udpSocket.bind((self.host, self.udp_port))
        self.tcpSocket.listen(5)
        
        self.inputs = [self.tcpSocket, self.udpSocket]
        
        print("Starting TCP server at " + self.host + ":" + str(self.tcp_port))
        print("Starting UDP server at " + self.host + ":" + str(self.udp_port))

    def mainLoop(self):
        print("Server is running...")
        while self.inputs:
            readable, writable, exceptional = select.select(self.inputs, [], [])
            for s in readable:
                if s is self.tcpSocket:
                    handle_new_TCP_connection(self.tcpSocket, self)
                elif s is self.udpSocket:
                    handle_UDP_message(self.udpSocket, self)
        self.tcpSocket.close()

