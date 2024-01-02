import threading
import logging
from .user_auth import UserAuth
from chat.common.exceptions import UserExistsException, UserNotFoundException, IncorrectPasswordException
from .udp_server import UDPServer
from chat.common.utils import sendTCPMessage, receiveTCPMessage, generate_random_secret

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
        self.peerUdpAddress = None
        self.online_in_rooms = set()
        
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
                            self.token = generate_random_secret()
                            response = f"login-success {self.token}"
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
                        self.lock.acquire()
                        try:
                            self.server_context.chatRooms[message[1]][self.username] = (self.tcpClientSocket, self.peerUdpAddress)
                            self.online_in_rooms.add(message[1])
                        finally:
                            self.lock.release()
                        print("Online peers in " + message[1] + ": " + str(self.server_context.chatRooms[message[1]]) + "\n")
                        response = f"room-joined"
                        # send room-joined and all the peers in the room as username-udp_address
                        # inform all the peers in the room that a new peer has joined through the tcp_socket of each of them
                        for username, (tcp_sock, udp_addr) in self.server_context.chatRooms[message[1]].items():
                            if username != self.username:
                                sendTCPMessage(tcp_sock, f"JOINED {self.username} {self.peerUdpAddress[0]}:{str(self.peerUdpAddress[1])}")
                                response += f" {username}:{udp_addr[0]}:{udp_addr[1]}"
                    sendTCPMessage(self.tcpClientSocket, response)
                elif message[0] == 'LEAVE-ROOM':
                    room_name = message[1]
                    self.leave_room(room_name)
                    sendTCPMessage(self.tcpClientSocket, f"room-left {room_name}")
            except OSError as oErr:
                logging.error("OSError: {0}".format(oErr))
            except Exception as e:
                print(e)
                break
        del self
    
    def leave_room(self, room_name):
        if room_name in self.online_in_rooms and room_name in self.server_context.chatRooms and self.username in self.server_context.chatRooms[room_name]:
            self.lock.acquire()
            try:
                del self.server_context.chatRooms[room_name][self.username]
                self.online_in_rooms.remove(room_name)
            finally:
                self.lock.release()
            # inform all the peers in the room that a peer has left through the tcp_socket of each of them
            for username, (tcp_sock, udp_addr) in self.server_context.chatRooms[room_name].items():
                sendTCPMessage(tcp_sock, f"LEFT {self.username}")

    def leave_all_rooms(self):
        for room_name in list(self.online_in_rooms):
            self.leave_room(room_name)

    def resetTimeout(self):
        self.udpServer.resetTimer()

