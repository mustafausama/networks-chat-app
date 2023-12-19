
#
#     ##  Implementation of registry
#     ##  150114822 - Eren Ulaş
#

import socket
import threading
import select
import logging
import db
from user_auth import UserAuth
from exceptions import UserExistsException, UserNotFoundException, IncorrectPasswordException

# This class is used to process the peer messages sent to registry
# for each peer connected to registry, a new client thread is created
class ClientThread(threading.Thread):
    # initializations for client thread
    def __init__(self, ip, port, tcpClientSocket):
        threading.Thread.__init__(self)
        # ip of the connected peer
        self.ip = ip
        # port number of the connected peer
        self.port = port
        # socket of the peer
        self.tcpClientSocket = tcpClientSocket
        # username, online status and udp server initializations
        self.username = None
        self.isOnline = True
        self.udpServer = None
        print("New thread started for " + ip + ":" + str(port))

    # main of the thread
    def run(self):
        # locks for thread which will be used for thread synchronization
        self.lock = threading.Lock()
        print("Connection from: " + self.ip + ":" + str(port))
        print("IP Connected: " + self.ip)
        
        while True:
            try:
                # waits for incoming messages from peers
                message = self.tcpClientSocket.recv(1024).decode().split()
                logging.info("Received from " + self.ip + ":" + str(self.port) + " -> " + " ".join(message))            
                if not message: continue
                if message[0] == "JOIN":
                    try:
                        UserAuth.register(message[1], message[2])
                        response = "join-success"
                    except UserExistsException:
                        response = "join-exist"
                    except Exception:
                        response = "server-error"
                    self.tcpClientSocket.send(response.encode())

                elif message[0] == "LOGIN":
                    try:
                        UserAuth.login(message[1], message[2])
                        if (self.ip, self.port) in onlinePeers:
                            response = 'login-online'
                        else:
                            self.username = message[1]
                            self.lock.acquire()
                            try:
                                tcpThreads[self.username] = self
                                onlinePeers[(self.ip, self.port)] = (self.username, message[3])
                            finally:
                                self.lock.release()
                            response = f"login-success {self.ip}:{self.port}"
                    except UserNotFoundException:
                        response = "login-account-not-exist"
                    except IncorrectPasswordException:
                        response = "login-wrong-password"
                    except Exception:
                        response = "server-error"

                    self.tcpClientSocket.send(response.encode())
                    if response.startswith('login-success'):
                        self.udpServer = UDPServer(self.username, self.tcpClientSocket)
                        self.udpServer.start()
                        self.udpServer.timer.start()

                elif message[0] == "LOGOUT":
                    self.lock.acquire()
                    try:
                        if self.username in tcpThreads:
                            del tcpThreads[self.username]
                        if (self.ip, self.port) in onlinePeers:
                            del onlinePeers[(self.ip, self.port)]
                    finally:
                        self.lock.release()
                    print(self.ip + ":" + str(self.port) + " is logged out")
                    self.tcpClientSocket.close()
                    if self.udpServer and self.udpServer.timer:
                        self.udpServer.timer.cancel()
                    break
            except OSError as oErr:
                logging.error("OSError: {0}".format(oErr)) 


    # function for resettin the timeout for the udp timer thread
    def resetTimeout(self):
        self.udpServer.resetTimer()

                            
# implementation of the udp server thread for clients
class UDPServer(threading.Thread):


    # udp server thread initializations
    def __init__(self, username, clientSocket):
        threading.Thread.__init__(self)
        self.username = username
        # timer thread for the udp server is initialized
        self.timer = threading.Timer(3, self.waitHelloMessage)
        self.tcpClientSocket: socket = clientSocket
    

    # if hello message is not received before timeout
    # then peer is disconnected
    def waitHelloMessage(self):
        lock = threading.Lock()
        lock.acquire()
        try:
            if self.username in tcpThreads:
                del tcpThreads[self.username]
            if (self.tcpClientSocket.getsockname()[0], self.tcpClientSocket.getsockname()[1]) in onlinePeers:
                del onlinePeers[(self.tcpClientSocket.getsockname()[0], self.tcpClientSocket.getsockname()[1])]
        finally:
            lock.release()
        self.tcpClientSocket.close()
        print("Removed " + self.username + " from online peers")


    # resets the timer for udp server
    def resetTimer(self):
        self.timer.cancel()
        self.timer = threading.Timer(3, self.waitHelloMessage)
        self.timer.start()


# tcp and udp server port initializations
print("Registy started...")

port = 15600
portUDP = 15500

# db initialization
db = db.DB()

# gets the ip address of this peer
# first checks to get it for windows devices
# if the device that runs this application is not windows
# it checks to get it for macos devices
hostname=socket.gethostname()
try:
    host=socket.gethostbyname(hostname)
except socket.gaierror:
    import netifaces as ni
    host = ni.ifaddresses('en0')[ni.AF_INET][0]['addr']



print("Registry IP address: " + host)
print("Registry port number: " + str(port))

# onlinePeers list for online account
onlinePeers = {}
# tcpThreads list for online client's thread
tcpThreads = {}

#tcp and udp socket initializations
tcpSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
tcpSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
udpSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
udpSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
tcpSocket.bind((host,port))
udpSocket.bind((host,portUDP))
tcpSocket.listen(5)

# input sockets that are listened
inputs = [tcpSocket, udpSocket]

# log file initialization
logging.basicConfig(filename="registry.log", level=logging.INFO)

# as long as at least a socket exists to listen registry runs
while inputs:

    print("Listening for incoming connections...")
    # monitors for the incoming connections
    readable, writable, exceptional = select.select(inputs, [], [])
    for s in readable:
        # if the message received comes to the tcp socket
        # the connection is accepted and a thread is created for it, and that thread is started
        if s is tcpSocket:
            tcpClientSocket, addr = tcpSocket.accept()
            newThread = ClientThread(addr[0], addr[1], tcpClientSocket)
            newThread.start()
        # if the message received comes to the udp socket
        elif s is udpSocket:
            # received the incoming udp message and parses it
            message, clientAddress = s.recvfrom(1024)
            message = message.decode().split()
            # checks if it is a hello message
            if message[0] == "HELLO":
                # checks if the account that this hello message 
                # is sent from is online
                username = message[1]
                ip, port = message[2].split(":")
                if message[1] in tcpThreads and (ip, int(port)) in onlinePeers:
                    tcpThreads[message[1]].resetTimeout()
                    print("Hello is received from " + message[1])
                    logging.info("Received from " + clientAddress[0] + ":" + str(clientAddress[1]) + " -> " + " ".join(message))
                else:
                    print(f"a7a error {message[1]} {ip}:{port}")
                    print(tcpThreads)
                    print(onlinePeers)
                    
# registry tcp socket is closed
tcpSocket.close()

