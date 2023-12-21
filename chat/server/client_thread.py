import threading
import logging
from .user_auth import UserAuth
from chat.common.exceptions import UserExistsException, UserNotFoundException, IncorrectPasswordException
from .udp_server import UDPServer

class ClientThread(threading.Thread):
    def __init__(self, ip, port, tcpClientSocket, server_context):
        threading.Thread.__init__(self)

        self.ip = ip
        self.port = port
        self.tcpClientSocket = tcpClientSocket
        
        self.username = None

        self.udpServer = None
        self.server_context = server_context
        
        print("New thread started for " + ip + ":" + str(port))

    def run(self):
        self.lock = threading.Lock()
        print("Connection from: " + self.ip + ":" + str(self.port))
        
        while True:
            try:
                try:
                    message = self.tcpClientSocket.recv(1024).decode().split()
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
                    self.tcpClientSocket.send(response.encode())

                elif message[0] == "LOGIN":
                    try:
                        UserAuth.login(message[1], message[2])
                        if (self.ip, self.port) in self.server_context.onlinePeers or message[1] in self.server_context.tcpThreads:
                            response = 'login-online'
                        else:
                            self.username = message[1]
                            self.lock.acquire()
                            try:
                                self.server_context.tcpThreads[self.username] = self
                                self.server_context.onlinePeers[(self.ip, self.port)] = (self.username, message[3])
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
                        self.udpServer = UDPServer(self.username, self.tcpClientSocket, self.server_context)
                        self.udpServer.start()
                        self.udpServer.timer.start()

                elif message[0] == "LOGOUT":
                    self.lock.acquire()
                    print(self.ip + ":" + str(self.port) + " is logged out")
                    self.tcpClientSocket.close()
                    if self.udpServer and self.udpServer.timer:
                        self.udpServer.timer.cancel()
                    try:
                        if self.username in self.server_context.tcpThreads:
                            del self.server_context.tcpThreads[self.username]
                        if (self.ip, self.port) in self.server_context.onlinePeers:
                            del self.server_context.onlinePeers[(self.ip, self.port)]
                    finally:
                        self.lock.release()
                    print("Logged out")
                    break
            except OSError as oErr:
                logging.error("OSError: {0}".format(oErr)) 
        del self

    def resetTimeout(self):
        self.udpServer.resetTimer()

