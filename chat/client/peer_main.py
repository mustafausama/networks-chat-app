from socket import *
import threading
import logging
import getpass
from .peer_server import *
from .peer_client import *
from chat.common.exceptions import *
from chat.common.utils import sendTCPMessage, receiveTCPMessage, get_input

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

def login(username, password, peerServerPort, tcpClientSocket):
    message = "LOGIN " + username + " " + password + " " + str(peerServerPort)
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

        self.tcpClientSocket = socket(AF_INET, SOCK_STREAM)
        self.tcpClientSocket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        self.tcpClientSocket.connect((self.registryName,self.registryPort))

        self.udpClientSocket = socket(AF_INET, SOCK_DGRAM)
        self.udpClientSocket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)

        _, self.registryUDPPort = inputRegAddress("Enter the registry UDP address (host:port): ")
        # login info of the peer
        self.loginCredentials = (None, None)
        # online status of the peer
        self.isOnline = False
        # server port number of this peer
        self.peerServerPort = None
        # server of this peer
        self.peerServer = None
        # client of this peer
        self.peerClient = None
        # timer initialization
        self.timer = None
    
    def mainLoop(self):
        choice = "0"
        # log file initialization
        logging.basicConfig(filename="peer.log", level=logging.INFO)
        # as long as the user is not logged out, asks to select an option in the menu
        while choice != "3":
            choice = get_input("Choose: \nCreate account: 1\nLogin: 2\nLogout: 3\nStart a chat: 4\n")

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
                    
                # asks for the port number for server's tcp socket
                peerServerPort = inputPortNumber()
                
                status, payload = login(username, password, peerServerPort, self.tcpClientSocket)
                # is user logs in successfully, peer variables are set
                if status is 1:
                    print("Logged in successfully...")
                    self.isOnline = True
                    self.loginCredentials = (username, password)
                    self.peerServerPort = peerServerPort
                    # creates the server thread for this peer, and runs it
                    self.peerServer = PeerServer(self.loginCredentials[0], self.peerServerPort)
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
           
           


            # if choice is 4 and user is online, then user is asked
            # to enter the username of the user that is wanted to be chatted
            elif choice is "4" and self.isOnline:
                username = get_input("Enter the username of user to start chat: ")
                searchStatus = self.searchUser(username)
                # if searched user is found, then its ip address and port number is retrieved
                # and a client thread is created
                # main process waits for the client thread to finish its chat
                if searchStatus is not None and searchStatus is not 0:
                    searchStatus = searchStatus.split(":")
                    self.peerClient = PeerClient(searchStatus[0], int(searchStatus[1]) , self.loginCredentials[0], self.peerServer, None)
                    self.peerClient.start()
                    self.peerClient.join()
            # if this is the receiver side then it will get the prompt to accept an incoming request during the main loop
            # that's why response is evaluated in main process not the server thread even though the prompt is printed by server
            # if the response is ok then a client is created for this peer with the OK message and that's why it will directly
            # sent an OK message to the requesting side peer server and waits for the user input
            # main process waits for the client thread to finish its chat
            elif choice == "OK" and self.isOnline:
                okMessage = "OK " + self.loginCredentials[0]
                logging.info("Send to " + self.peerServer.connectedPeerIP + " -> " + okMessage)
                self.peerServer.connectedPeerSocket.send(okMessage.encode())
                self.peerClient = PeerClient(self.peerServer.connectedPeerIP, self.peerServer.connectedPeerPort , self.loginCredentials[0], self.peerServer, "OK")
                self.peerClient.start()
                self.peerClient.join()
            # if user rejects the chat request then reject message is sent to the requester side
            elif choice == "REJECT" and self.isOnline:
                self.peerServer.connectedPeerSocket.send("REJECT".encode())
                self.peerServer.isChatRequested = 0
                logging.info("Send to " + self.peerServer.connectedPeerIP + " -> REJECT")
            # if choice is cancel timer for hello message is cancelled
            elif choice == "CANCEL":
                self.timer.cancel()
                break
        # if main process is not ended with cancel selection
        # socket of the client is closed
        if choice != "CANCEL":
            self.tcpClientSocket.close()

    # # account creation function
    # def createAccount(self, username, password):
    #     # join message to create an account is composed and sent to registry
    #     # if response is success then informs the user for account creation
    #     # if response is exist then informs the user for account existence
    #     message = "JOIN " + username + " " + password
    #     logging.info("Send to " + self.registryName + ":" + str(self.registryPort) + " -> " + message)
    #     self.tcpClientSocket.send(message.encode())
    #     response = self.tcpClientSocket.recv(1024).decode()
    #     logging.info("Received from " + self.registryName + " -> " + response)
    #     if response == "join-success":
    #         print("Account created...")
    #     elif response == "join-exist":
    #         print("choose another username or login...")

    # # login function
    # def login(self, username, password, peerServerPort):
    #     # a login message is composed and sent to registry
    #     # an integer is returned according to each response
    #     message = "LOGIN " + username + " " + password + " " + str(peerServerPort)
    #     logging.info("Send to " + self.registryName + ":" + str(self.registryPort) + " -> " + message)
    #     self.tcpClientSocket.send(message.encode())
    #     response = self.tcpClientSocket.recv(1024).decode()
    #     logging.info("Received from " + self.registryName + " -> " + response)
    #     if response.startswith("login-success"):
    #         print("Logged in successfully...")
    #         return 1, response.split()[1]
    #     elif response == "login-account-not-exist":
    #         print("Account does not exist...")
    #         return 0, ""
    #     elif response == "login-online":
    #         print("Account is already online...")
    #         return 2, ""
    #     elif response == "login-wrong-password":
    #         print("Wrong password...")
    #         return 3, ""
    
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
            print(username + " is found successfully...")
            return response[1]
        elif response[0] == "search-user-not-online":
            print(username + " is not online...")
            return 0
        elif response[0] == "search-user-not-found":
            print(username + " is not found")
            return None
    
    # function for sending hello message
    # a timer thread is used to send hello messages to udp socket of registry
    def sendHelloMessage(self, payload):
        message = f"HELLO {self.loginCredentials[0]} {payload}"
        logging.info("Send to " + self.registryName + ":" + str(self.registryUDPPort) + " -> " + message)
        self.udpClientSocket.sendto(message.encode(), (self.registryName, self.registryUDPPort))
        self.timer = threading.Timer(1, self.sendHelloMessage, [payload])
        self.timer.start()
