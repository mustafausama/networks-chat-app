import threading

class UDPServer(threading.Thread):

    # udp server thread initializations
    def __init__(self, username, clientSocket, server_context):
        threading.Thread.__init__(self)
        self.username = username
        # timer thread for the udp server is initialized
        self.timer = threading.Timer(3, self.waitHelloMessage)
        self.tcpClientSocket = clientSocket
        self.server_context = server_context

    # if hello message is not received before timeout
    # then peer is disconnected
    def waitHelloMessage(self):
        lock = threading.Lock()
        print("Timeout for " + self.username)
        lock.acquire()
        try:
            if self.username in self.server_context.tcpThreads:
                self.server_context.tcpThreads[self.username].udpServer = None
                self.server_context.tcpThreads[self.username].leave_all_rooms()
                del self.server_context.tcpThreads[self.username]
        finally:
            lock.release()
        self.tcpClientSocket.close()
        print("Removed " + self.username + " from online peers")

    # resets the timer for udp server
    def resetTimer(self):
        # print("Resetting timer for " + self.username)
        self.timer.cancel()
        self.timer = threading.Timer(3, self.waitHelloMessage)
        self.timer.start()
