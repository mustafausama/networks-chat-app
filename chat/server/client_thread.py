import threading
import logging
from .user_auth import UserAuth
from chat.common.exceptions import UserExistsException, UserNotFoundException, IncorrectPasswordException
from .udp_server import UDPServer
from chat.common.utils import sendTCPMessage, receiveTCPMessage
import socket

class ClientThread(threading.Thread):
    def __init__(self, ip, port, tcpClientSocket, server_context):
        threading.Thread.__init__(self)

        self.ip = ip
        self.port = port
        self.tcpClientSocket = tcpClientSocket
        
        self.username = None

        self.udpServer = None
        self.server_context = server_context
        
        self.peerServerAddress = None
        
        print("New thread started for " + ip + ":" + str(port))

    def run(self):
        self.lock = threading.Lock()
        print("Connection from: " + self.ip + ":" + str(self.port))
        
        while True:
            try:
                try:
                    message = receiveTCPMessage(self.tcpClientSocket).split()
                except:
                    logging.error("TCP Client error")
                    break

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
                    sendTCPMessage(self.tcpClientSocket, response)

                elif message[0] == "LOGIN":
                    try:
                        UserAuth.login(message[1], message[2])
                        # if (self.ip, self.port) in self.server_context.onlinePeers or message[1] in self.server_context.tcpThreads:
                        if message[1] in self.server_context.tcpThreads:
                            response = 'login-online'
                        else:
                            self.username = message[1]
                            self.peerServerAddress = message[3]
                            self.lock.acquire()
                            try:
                                self.server_context.tcpThreads[self.username] = self
                                # self.server_context.onlinePeers[(self.ip, self.port)] = (self.username, message[3])
                            finally:
                                self.lock.release()
                            response = f"login-success {self.ip}:{self.port}"
                    except UserNotFoundException:
                        response = "login-account-not-exist"
                    except IncorrectPasswordException:
                        response = "login-wrong-password"
                    except Exception:
                        response = "server-error"

                    sendTCPMessage(self.tcpClientSocket, response)
                    if response.startswith('login-success'):
                        self.udpServer = UDPServer(self.username, self.tcpClientSocket, self.server_context)
                        self.udpServer.start()
                        self.udpServer.timer.start()
                    else:
                        self.peerServerAddress = None

                elif message[0] == "LOGOUT":
                    self.lock.acquire()
                    print(self.ip + ":" + str(self.port) + " is logged out")
                    self.tcpClientSocket.close()
                    if self.udpServer and self.udpServer.timer:
                        self.udpServer.timer.cancel()
                    try:
                        if self.username in self.server_context.tcpThreads:
                            del self.server_context.tcpThreads[self.username]
                        # if (self.ip, self.port) in self.server_context.onlinePeers:
                        #     del self.server_context.onlinePeers[(self.ip, self.port)]
                    finally:
                        self.lock.release()
                    print("Logged out")
                    break
                elif message[0] == 'LIST-USERS':
                    self.lock.acquire()
                    try:
                        users = list(self.server_context.tcpThreads.keys())
                    finally:
                        self.lock.release()
                    response = 'list-users ' + ' '.join(users)
                    sendTCPMessage(self.tcpClientSocket, response)
                elif message[0] == 'SEARCH':
                    if not UserAuth.fine_user(message[1]):
                        response = 'search-user-not-found'
                    elif message[1] not in self.server_context.tcpThreads:
                        response = 'search-user-not-online'
                    else:
                        response = 'search-success ' + self.server_context.tcpThreads[message[1]].peerServerAddress
                    sendTCPMessage(self.tcpClientSocket, response)
                elif message[0] == 'CREATE-ROOM':
                    if message[1] not in self.server_context.chatRooms:
                        self.lock.acquire()
                        try:
                            self.server_context.chatRooms[message[1]] = {}
                        finally:
                            self.lock.release()
                        response = 'room-created'
                    else:
                        response = 'room-exist'
                    sendTCPMessage(self.tcpClientSocket, response)
                elif message[0] == 'LIST-ROOMS':
                    message = 'list-rooms ' + ' '.join(self.server_context.chatRooms.keys())
                    sendTCPMessage(self.tcpClientSocket, message)
                elif message[0] == 'JOIN-ROOM':
                    if message[1] not in self.server_context.chatRooms:
                        response = 'room-not-found'
                    else:
                        tcp_address = message[2]
                        udp_address = message[3]
                        secret = message[4]
                        # establish tcp connection and send secret
                        print("TCP socket at " + tcp_address + " is connecting...")
                        print("UDP socket at " + udp_address + " is connecting...")
                        tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        tcp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                        tcp_socket.connect((tcp_address.split(':')[0], int(tcp_address.split(':')[1])))
                        print("Sending secret to " + tcp_address + "...")
                        sendTCPMessage(tcp_socket, secret)
                        # store the tcp socket and the udp address
                        self.lock.acquire()
                        try:
                            self.server_context.chatRooms[message[1]][self.username] = (tcp_socket, (udp_address.split(':')[0], int(udp_address.split(':')[1])))
                        finally:
                            self.lock.release()
                        print("Online peers in " + message[1] + ": " + str(self.server_context.chatRooms[message[1]]) + "\n")
                        response = f"room-joined"
                        # send room-joined and all the peers in the room as username-udp_address
                        # inform all the peers in the room that a new peer has joined through the tcp_socket of each of them
                        for username, (tcp_sock, udp_addr) in self.server_context.chatRooms[message[1]].items():
                            if username != self.username:
                                sendTCPMessage(tcp_sock, f"JOINED {self.username} {udp_address}")
                                response += f" {username}:{udp_addr[0]}:{udp_addr[1]}"
                        # for username in self.server_context.chatRooms[message[1]]:
                        #     if username != self.username:
                        #         udp_address = self.server_context.chatRooms[message[1]][username][1]
                        #         message += f" {username}-{udp_address}"
                        #         sendTCPMessage(tcp_socket, f"JOINED {self.username} {udp_address}")
                        # for username, (tcp_socket, udp_address) in self.server_context.chatRooms[message[1]].items():
                        #     if username != self.username:
                        #         sendTCPMessage(tcp_socket, f"JOINED {self.username} {udp_address}")
                    sendTCPMessage(self.tcpClientSocket, response)
                elif message[0] == 'LEAVE-ROOM':
                    room_name = message[1]
                    if room_name not in self.server_context.chatRooms:
                        response = 'room-not-found'
                    elif self.username not in self.server_context.chatRooms[room_name]:
                        response = 'room-not-joined'
                    else:
                        self.lock.acquire()
                        try:
                            del self.server_context.chatRooms[room_name][self.username]
                        finally:
                            self.lock.release()
                        response = 'room-left'
                        # inform all the peers in the room that a peer has left through the tcp_socket of each of them
                        for username, (tcp_sock, udp_addr) in self.server_context.chatRooms[room_name].items():
                            sendTCPMessage(tcp_sock, f"LEFT {self.username}")
            except OSError as oErr:
                logging.error("OSError: {0}".format(oErr))
            except Exception as e:
                print(e)
                break
        del self

    def resetTimeout(self):
        self.udpServer.resetTimer()

