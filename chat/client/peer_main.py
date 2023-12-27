from socket import *
import threading
import logging
import getpass
from .peer_server import *
from .peer_client import *
from chat.common.exceptions import *
from chat.common.utils import sendTCPMessage, receiveTCPMessage, get_input, get_hostname, find_available_port
from threading import Thread
from .peer_room import PeerRoom, broadcast_message

def inputRegAddress(msg):
    print(msg)
    flag = False
    while True:
        if flag: print("Please enter a valid address formatted as (host:port): ")
        else: flag = True
        regAddress = get_input()
        if not regAddress: continue
        if len(regAddress.split(":")) != 2: continue
        host, port = regAddress.split(":")
        if not host.replace(".", "").isdigit(): continue
        if len(host.split(".")) != 4: continue
        for i in host.split("."):
            if int(i) > 255 or int(i) < 0: continue
        if not port.isdigit(): continue
        port = int(port)
        if port > 65535 or port < 0: continue
        break
    return regAddress.split(":")[0], int(regAddress.split(":")[1])

def inputUsername():
    username = get_input("Username: ")
    while not username:
        username = get_input("Please enter a valid username: ")
    return username

def inputPassword():
    password = getpass.getpass("Password: ")
    while not password:
        password = getpass.getpass("Password field must be filled: ")
    return password

def inputPortNumber():
    portNumber = get_input("Enter a port number for peer server: ")
    while not portNumber or not portNumber.isdigit() or int(portNumber) > 65535 or int(portNumber) < 0:
        portNumber = get_input("Please enter a valid port number: ")
    return int(portNumber)

def createAccount(username, password, tcpClientSocket):
    message = "JOIN " + username + " " + password
    sendTCPMessage(tcpClientSocket, message)
    response = receiveTCPMessage(tcpClientSocket)
    return response

def login(username, password, peerServerAddress, tcpClientSocket):
    message = "LOGIN " + username + " " + password + " " + str(peerServerAddress)
    sendTCPMessage(tcpClientSocket, message)
    response = receiveTCPMessage(tcpClientSocket)

    if response.startswith("login-success"):
        return 1, response.split()[1]
    elif response == "login-account-not-exist":
        return 0, ""
    elif response == "login-online":
        return 2, ""
    elif response == "login-wrong-password":
        return 3, ""

class PeerMain:

    # peer initializations
    def __init__(self):
        self.registryName, self.registryPort = inputRegAddress("Enter the registry TCP address (host:port): ")
        self.registryPort = 15600
        self.tcpClientSocket = socket(AF_INET, SOCK_STREAM)
        self.tcpClientSocket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        self.tcpClientSocket.connect((self.registryName,self.registryPort))
        # self.tcpClientSocket.listen(5)

        self.udpClientSocket = socket(AF_INET, SOCK_DGRAM)
        self.udpClientSocket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)

        _, self.registryUDPPort = inputRegAddress("Enter the registry UDP address (host:port): ")
        self.loginCredentials = (None, None)
        self.isOnline = False
        self.peerServerPort = None
        self.peerServer = None
        self.peerClient = None
        self.timer = None
        
        self.isInChatRoom = False

        self.roomTCPSocket = None
        self.roomUDPSocket = None
        self.roomTCPThread = None
        self.roomUDPThread = None
        self.online_room_peers = {}

    def mainLoop(self):
        choice = "0"
        # log file initialization
        logging.basicConfig(filename="peer.log", level=logging.INFO)
        # as long as the user is not logged out, asks to select an option in the menu
        while choice != "3":
            choice = get_input("\
Choose: \n\
Create account: 1\n\
Login: 2\n\
Logout: 3\n\
Online Users: 4\n\
Private Chat: 5\n\
Create a chat room: 6\n\
List Chat rooms: 7\n\
Join a chat room: 8\n")

            if choice == "1":
                username = inputUsername()
                password = inputPassword()
                response = createAccount(username, password, self.tcpClientSocket)
                if response == "join-success":
                    print("Account created...")
                elif response == "join-exist":
                    print("choose another username or login...")

            elif choice is "2" and not self.isOnline:
                username = inputUsername()
                password = inputPassword()
                peerServerHost = get_hostname()
                peerServerPort = inputPortNumber()
                
                status, payload = login(username, password, f"{peerServerHost}:{peerServerPort}", self.tcpClientSocket)
                # is user logs in successfully, peer variables are set
                if status is 1:
                    print("Logged in successfully...")
                    self.isOnline = True
                    self.loginCredentials = (username, password)
                    self.peerServerPort = peerServerPort
                    # creates the server thread for this peer, and runs it
                    self.peerServer = PeerServer(self.loginCredentials[0], self.peerServerPort, self)
                    self.peerServer.start()
                    # hello message is sent to registry
                    self.sendHelloMessage(payload)
                elif status is 0:
                    print("Account does not exist...")
                elif status is 2:
                    print("Account is already online...")
                elif status is 3:
                    print("Wrong password...")
            # if choice is 3 and user is logged in, then user is logged out
            # and peer variables are set, and server and client sockets are closed
            elif choice is "3" and self.isOnline:
                self.logout(1)
                self.isOnline = False
                self.loginCredentials = (None, None)
                self.peerServer.isOnline = False
                self.peerServer.tcpServerSocket.close()
                if self.peerClient is not None:
                    self.peerClient.tcpClientSocket.close()
                print("Logged out successfully")
            # is peer is not logged in and exits the program
            elif choice is "3":
                self.logout(2)
            elif choice is "4" and self.isOnline:
                message = "LIST-USERS"
                logging.info("Send to " + self.registryName + ":" + str(self.registryPort) + " -> " + message)
                self.tcpClientSocket.send(message.encode())
                response = self.tcpClientSocket.recv(1024).decode().split()
                logging.info("Received from " + self.registryName + " -> " + " ".join(response))
                if response[0] == "list-users":
                    print("Online users:")
                    for i in range(1, len(response)):
                        print(response[i])

            elif choice is "5" and self.isOnline:
                username = inputUsername()

                status, payload = self.searchUser(username)

                if status is 1:
                    print("User is found and is online. Do you want to chat with " + username + "? (y/n)")
                    answer = get_input()
                    if answer == "y":
                        ip, port = payload.split(":")
                        # creates the client thread for this peer, and runs it
                        print("Creating peer client at " + ip + ":" + port)
                        self.peerClient = PeerClient(ip, int(port), self.loginCredentials[0], self.peerServer, None)
                        self.peerClient.start()
                        # sends a chat request to the other peer
                        self.peerClient.join()
                    else:
                        print("Chat request is cancelled...")
                elif status is 2:
                    print("User is not online...")
                elif status is 3:
                    print("User is not found...")
            elif choice == "OK" and self.isOnline:
                okMessage = "OK " + self.loginCredentials[0]
                logging.info("Send to " + self.peerServer.connectedPeerIP + " -> " + okMessage)
                self.peerServer.connectedPeerSocket.send(okMessage.encode())
                print("Creating peer client at " + self.peerServer.connectedPeerIP + ":" + str(self.peerServer.connectedPeerPort))
                self.peerClient = PeerClient(self.peerServer.connectedPeerIP, self.peerServer.connectedPeerPort , self.loginCredentials[0], self.peerServer, "OK")
                self.peerClient.start()
                self.peerClient.join()
            elif choice == "REJECT" and self.isOnline:
                self.peerServer.connectedPeerSocket.send("REJECT".encode())
                self.peerServer.isChatRequested = 0
                logging.info("Send to " + self.peerServer.connectedPeerIP + " -> REJECT")
            elif choice == "6" and self.isOnline:
                if self.isInChatRoom:
                    print("You are already in a chat room...")
                else:
                    room_name = get_input("Enter a name for the chat room: ")
                    while not room_name:
                        room_name = get_input("Please enter a valid name for the chat room: ")
                    message = "CREATE-ROOM "+room_name
                    self.tcpClientSocket.send(message.encode())
                    response = self.tcpClientSocket.recv(1024).decode().split()
                    if response[0] == "room-created":
                        print("Chat room is created...")
                    else:
                        print("Chat room already exists...")
            elif choice == "7" and self.isOnline:
                message = "LIST-ROOMS"
                self.tcpClientSocket.send(message.encode())
                response = self.tcpClientSocket.recv(1024).decode().split()
                if response[0] == "list-rooms":
                    print("Chat rooms:")
                    for i in range(1, len(response)):
                        print(response[i])
            elif choice == "8" and self.isOnline:
                if self.isInChatRoom:
                    print("You are already in a chat room...")
                else:
                    room_name = get_input("Enter the name of the chat room: ")
                    while not room_name:
                        room_name = get_input("Please enter a valid name for the chat room: ")
                    message = f"JOIN-ROOM {room_name}"
                    print("Message: "+message)
                    self.tcpClientSocket.send(message.encode())
                    response = self.tcpClientSocket.recv(1024).decode().split()
                    room = PeerRoom(self)
                    room.start_threads()
                    if response[0] == "room-joined":
                        self.isInChatRoom = True
                        # add the peers in the chat room to the online_room_peers
                        print("Online peers in " + room_name + ": " + str(response[1:]) + "\n")
                        for peer in response[1:]:
                            username, addressIP, addressPort = peer.split(":")
                            print("User " + username + " joined the room from " + str((addressIP, int(addressPort))) + ".")
                            self.online_room_peers[username] = (addressIP, int(addressPort))
                        print("Joined "+room_name+" chat room...")
                        userMessage = get_input()
                        while userMessage != ":q":
                            broadcast_message(self, userMessage)
                            userMessage = get_input()
                        # send LEAVE-ROOM
                        self.tcpClientSocket.send(f"LEAVE-ROOM {room_name}".encode())
                        room.stop_threads()
                        self.isInChatRoom = False
                        self.online_room_peers.clear()
                        print("Left "+room_name+" chat room...")

                    elif response[0] == "room-not-found":
                        print("Chat room is not found...")
                    elif response[0] == "room-full":
                        print("Chat room is full...")
                    elif response[0] == "room-already-joined":
                        print("You are already in this chat room...")

            elif choice == "CANCEL":
                self.timer.cancel()
                break
            else:
                print("Please select a valid option...")
        # if main process is not ended with cancel selection
        # socket of the client is closed
        if choice != "CANCEL":
            self.tcpClientSocket.close()
    
    # logout function
    def logout(self, option):
        # a logout message is composed and sent to registry
        # timer is stopped
        if option == 1:
            message = "LOGOUT " + self.loginCredentials[0]
            self.timer.cancel()
        else:
            message = "LOGOUT"
        logging.info("Send to " + self.registryName + ":" + str(self.registryPort) + " -> " + message)
        self.tcpClientSocket.send(message.encode())
        

    # function for searching an online user
    def searchUser(self, username):
        # a search message is composed and sent to registry
        # custom value is returned according to each response
        # to this search message
        message = "SEARCH " + username
        logging.info("Send to " + self.registryName + ":" + str(self.registryPort) + " -> " + message)
        self.tcpClientSocket.send(message.encode())
        response = self.tcpClientSocket.recv(1024).decode().split()
        print(response)
        logging.info("Received from " + self.registryName + " -> " + " ".join(response))
        if response[0] == "search-success":
            return 1, response[1]
        elif response[0] == "search-user-not-online":
            return 2, ""
        elif response[0] == "search-user-not-found":
            return 3, ""
    
    # function for sending hello message
    # a timer thread is used to send hello messages to udp socket of registry
    def sendHelloMessage(self, payload):
        message = f"HELLO {self.loginCredentials[0]} {payload}"
        logging.info("Send to " + self.registryName + ":" + str(self.registryUDPPort) + " -> " + message)
        self.udpClientSocket.sendto(message.encode(), (self.registryName, self.registryUDPPort))
        self.timer = threading.Timer(1, self.sendHelloMessage, [payload])
        self.timer.start()
