from socket import *
import threading
import logging
import getpass
from .peer_server import *
from .peer_client import *
from chat.common.exceptions import *
from chat.common.utils import sendTCPMessage, receiveTCPMessage, get_input, get_hostname, find_available_port, print_colored_text, format_text, clear_last_console_line
from threading import Thread
from .peer_room import PeerRoom, broadcast_message

def inputRegAddress(msg):
    print_colored_text(msg, 'yellow')
    flag = False
    while True:
        if flag: print_colored_text("Please enter a valid address formatted as (host:port): ", 'red')
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
    username = get_input("Username: ", 'yellow')
    while not username:
        username = get_input("Please enter a valid username: ", 'red')
    return username

def inputPassword():
    password = getpass.getpass("Password: ")
    while not password:
        password = getpass.getpass("Password field must be filled: ")
    return password

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
        try:
            with open("tcp.config", "r") as f:
                regAddress = f.readline()
                if regAddress:
                    print_colored_text("Registry tcp address is read from tcp.config file...", 'green')
                    regAddress = regAddress.strip().split(":")
                    self.registryName, self.registryPort = regAddress[0], int(regAddress[1])
                else:
                    raise FileNotFoundError()
        except FileNotFoundError:
            self.registryName, self.registryPort = inputRegAddress("Enter the registry TCP address (host:port): ")

        self.tcpClientSocket = socket(AF_INET, SOCK_STREAM)
        self.tcpClientSocket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        print("TCP connecting to " + self.registryName + ":" + str(self.registryPort))
        self.tcpClientSocket.connect((self.registryName,self.registryPort))
        # self.tcpClientSocket.listen(5)

        self.udpClientSocket = socket(AF_INET, SOCK_DGRAM)
        self.udpClientSocket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)


        try:
            with open("udp.config", "r") as f:
                regAddress = f.readline()
                if regAddress:
                    print_colored_text("Registry udp address is read from udp.config file...", 'green')
                    regAddress = regAddress.strip().split(":")
                    _, self.registryUDPPort = regAddress[0], int(regAddress[1])
                else:
                    raise FileNotFoundError()
        except FileNotFoundError:
            _, self.registryUDPPort = inputRegAddress("Enter the registry UDP address (host:port): ")

        print("UDP Saving registry address - " + self.registryName + ":" + str(self.registryUDPPort))


        try:
            with open("testing_flag.txt", "r") as f:
                self.testing = True
        except FileNotFoundError:
            self.testing = False

        # _, self.registryUDPPort = inputRegAddress("Enter the registry UDP address (host:port): ")
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

    def print_coices_colored(self):
        # Print the choices in different colors (each choice with a different color). All choices on one line. Check if the user is online or not.
        # each choice with a different color
        if not self.isOnline:
            print_colored_text("You're not logged in.", 'red', end=' - ')
            print_colored_text("Register (1)", 'green', end=' ')
            print_colored_text("Login (2)", 'blue', end='\n')
        else:
            print_colored_text("You're logged in.", 'green', end=' - ')
            print_colored_text("Logout (3)", 'red', end=' ')
            print_colored_text("Online Users (4)", 'blue', end=' ')
            print_colored_text("Private Chat (5)", 'yellow', end=' ')
            print_colored_text("Create room (6)", 'cyan', end=' ')
            print_colored_text("List rooms (7)", 'purple', end=' ')
            print_colored_text("Join room (8)", 'light_red', end='\n')

    def mainLoop(self):
        choice = "0"
        # log file initialization
        logging.basicConfig(filename="peer.log", level=logging.INFO)
        # as long as the user is not logged out, asks to select an option in the menu
        if self.testing:
            while True:
                pass
        while choice != "3":
            self.print_coices_colored()
            choice = get_input()

            if choice == "1":
                username = inputUsername()
                password = inputPassword()
                response = createAccount(username, password, self.tcpClientSocket)
                if response == "join-success":
                    print_colored_text("Account created...", 'green')
                elif response == "join-exist":
                    print_colored_text("choose another username or login...", 'red')

            elif choice == "2" and not self.isOnline:
                username = inputUsername()
                password = inputPassword()
                peerServerHost = get_hostname()
                peerServerPort = find_available_port(peerServerHost, 10000, 20000)
                
                status, payload = login(username, password, f"{peerServerHost}:{peerServerPort}", self.tcpClientSocket)
                # is user logs in successfully, peer variables are set
                if status == 1:
                    print_colored_text("Logged in successfully...", 'green')
                    self.isOnline = True
                    self.loginCredentials = (username, password)
                    self.peerServerPort = peerServerPort
                    # creates the server thread for this peer, and runs it
                    self.peerServer = PeerServer(self.loginCredentials[0], self.peerServerPort, self)
                    self.peerServer.start()
                    # hello message is sent to registry
                    self.sendHelloMessage(payload)
                elif status == 0:
                    print_colored_text("Account does not exist...", 'red')
                elif status == 2:
                    print_colored_text("Account is already online...", 'red')
                elif status == 3:
                    print_colored_text("Wrong password...", 'red')
            # if choice is 3 and user is logged in, then user is logged out
            # and peer variables are set, and server and client sockets are closed
            elif choice == "3" and self.isOnline:
                self.logout(1)
                self.isOnline = False
                self.loginCredentials = (None, None)
                self.peerServer.isOnline = False
                self.peerServer.tcpServerSocket.close()
                if self.peerClient is not None:
                    self.peerClient.tcpClientSocket.close()
                print_colored_text("Logged out successfully", 'green')
            # is peer is not logged in and exits the program
            elif choice == "3":
                self.logout(2)
            elif choice == "4" and self.isOnline:
                message = "LIST-USERS"
                logging.info("Send to " + self.registryName + ":" + str(self.registryPort) + " -> " + message)
                self.tcpClientSocket.send(message.encode())
                response = self.tcpClientSocket.recv(1024).decode().split()
                logging.info("Received from " + self.registryName + " -> " + " ".join(response))
                if response[0] == "list-users":
                    print_colored_text("Online users:", 'green')
                    for i in range(1, len(response)):
                        print_colored_text(response[i], 'cyan')

            elif choice == "5" and self.isOnline:
                username = inputUsername()
                while username == self.loginCredentials[0]:
                    print_colored_text("You cannot chat with yourself...", 'red')
                    username = inputUsername()

                status, payload = self.searchUser(username)

                if status == 1:
                    print_colored_text("User is found and is online. Do you want to chat with " + username + "? (y/n)", 'yellow')
                    answer = get_input()
                    if answer == "y":
                        ip, port = payload.split(":")
                        # creates the client thread for this peer, and runs it
                        print_colored_text("Creating peer client at " + ip + ":" + port, 'green')
                        self.peerClient = PeerClient(ip, int(port), self.loginCredentials[0], self.peerServer, None)
                        self.peerClient.start()
                        # sends a chat request to the other peer
                        self.peerClient.join()
                    else:
                        print_colored_text("Chat request is cancelled...", 'red')
                elif status == 2:
                    print_colored_text("User is not online...", 'red')
                elif status == 3:
                    print_colored_text("User is not found...", 'red')
            elif choice == "OK" and self.isOnline:
                okMessage = "OK " + self.loginCredentials[0]
                logging.info("Send to " + self.peerServer.connectedPeerIP + " -> " + okMessage)
                self.peerServer.connectedPeerSocket.send(okMessage.encode())
                print_colored_text("Creating peer client at " + self.peerServer.connectedPeerIP + ":" + str(self.peerServer.connectedPeerPort), 'green')
                self.peerClient = PeerClient(self.peerServer.connectedPeerIP, self.peerServer.connectedPeerPort , self.loginCredentials[0], self.peerServer, "OK")
                self.peerClient.start()
                self.peerClient.join()
            elif choice == "REJECT" and self.isOnline:
                self.peerServer.connectedPeerSocket.send("REJECT".encode())
                self.peerServer.isChatRequested = 0
                logging.info("Send to " + self.peerServer.connectedPeerIP + " -> REJECT")
            elif choice == "6" and self.isOnline:
                if self.isInChatRoom:
                    print_colored_text("You are already in a chat room...", 'red')
                else:
                    room_name = get_input("Enter a name for the chat room: ", 'yellow')
                    while not room_name:
                        room_name = get_input("Please enter a valid name for the chat room: ", 'red')
                    message = "CREATE-ROOM "+room_name
                    self.tcpClientSocket.send(message.encode())
                    response = self.tcpClientSocket.recv(1024).decode().split()
                    if response[0] == "room-created":
                        print_colored_text("Chat room is created...", 'green')
                    else:
                        print_colored_text("Chat room already exists...", 'red')
            elif choice == "7" and self.isOnline:
                message = "LIST-ROOMS"
                self.tcpClientSocket.send(message.encode())
                response = self.tcpClientSocket.recv(1024).decode().split()
                if response[0] == "list-rooms":
                    print_colored_text("Chat rooms:", 'green')
                    for i in range(1, len(response)):
                        print_colored_text(response[i], 'cyan')
            elif choice == "8" and self.isOnline:
                if self.isInChatRoom:
                    print_colored_text("You are already in a chat room...", 'red')
                else:
                    room_name = get_input("Enter the name of the chat room: ", 'yellow')
                    while not room_name:
                        room_name = get_input("Please enter a valid name for the chat room: ", 'red')
                    message = f"JOIN-ROOM {room_name}"
                    self.tcpClientSocket.send(message.encode())
                    response = self.tcpClientSocket.recv(1024).decode().split()
                    room = PeerRoom(self)
                    room.start_thread()
                    if response[0] == "room-joined":
                        self.isInChatRoom = True
                        # add the peers in the chat room to the online_room_peers
                        print_colored_text("Online peers in " + room_name + ": ", 'green')
                        for peer in response[1:]:
                            username, addressIP, addressPort = peer.split(":")
                            print_colored_text("User " + username + " is online in the room from " + str((addressIP, int(addressPort))) + ".", 'cyan')
                            self.online_room_peers[username] = (addressIP, int(addressPort))
                        print_colored_text("You joined "+room_name+" chat room...", 'green')
                        userMessage = get_input()
                        while not userMessage:
                            userMessage = get_input()
                        while userMessage != ":q":
                            clear_last_console_line()
                            print_colored_text(self.loginCredentials[0]+": ", 'green', end='')
                            print(format_text(userMessage))
                            broadcast_message(self, userMessage)
                            userMessage = get_input()
                            while not userMessage:
                                userMessage = get_input()
                        # send LEAVE-ROOM
                        self.tcpClientSocket.send(f"LEAVE-ROOM {room_name}".encode())
                        room.stop_thread()
                        self.isInChatRoom = False
                        self.online_room_peers.clear()
                        print_colored_text("Left "+room_name+" chat room...", 'yellow')

                    elif response[0] == "room-not-found":
                        print_colored_text("Chat room is not found...", 'red')
                    elif response[0] == "room-full":
                        print_colored_text("Chat room is full...", 'red')
                    elif response[0] == "room-already-joined":
                        print_colored_text("You are already in this chat room...", 'red')

            elif choice == "CANCEL":
                self.timer.cancel()
                break
            else:
                print_colored_text("Please select a valid option...", 'red')
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
