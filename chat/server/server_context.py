import socket, select, logging
from .client_thread import ClientThread
from chat.common.utils import find_available_port, get_hostname

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
        token = message[2]
        # if username in server_context.tcpThreads and (ip, int(port)) in server_context.onlinePeers:
        if username in server_context.tcpThreads and server_context.tcpThreads[username].token == token:
            server_context.tcpThreads[username].resetTimeout()
            if server_context.tcpThreads[username].peerUdpAddress != clientAddress:
                server_context.tcpThreads[username].peerUdpAddress = clientAddress

class ServerContext:
    PORT_BASE = 15500
    def __init__(self) -> None:
        self.host = get_hostname()


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

    def mainLoop(self, testing = None):
        print("Server is running...")
        if testing is not None:
            import threading
            testing['registryPID'] = threading.get_native_id()
            testing['identity'] = threading.get_ident()
            testing['tcp_port'] = self.tcp_port
            testing['udp_port'] = self.udp_port
            testing['host'] = self.host
        while self.inputs:
            readable, writable, exceptional = select.select(self.inputs, [], [])
            for s in readable:
                if s is self.tcpSocket:
                    handle_new_TCP_connection(self.tcpSocket, self)
                    if testing is not None:
                        testing['log'] = "New TCP connection"
                elif s is self.udpSocket:
                    handle_UDP_message(self.udpSocket, self)
        self.tcpSocket.close()

