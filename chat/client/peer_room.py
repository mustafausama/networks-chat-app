from chat.common.utils import receiveTCPMessage
import logging
import select
import threading

class PeerRoom:
    def __init__(self, main_context):
        self.stop = False
        self.roomTCPThread = threading.Thread(target=self.handle_tcp_chat_room, args=(main_context,))
        self.roomUDPThread = threading.Thread(target=self.handle_udp_chat_room, args=(main_context,))

    def handle_tcp_chat_room(self, main_context):
        while True and not self.stop:
            try:
                try:
                    message = receiveTCPMessage(main_context.tcpClientSocket).split()
                except:
                    logging.error("TCP Client error")
                    break
                if(message[0] == 'room-left'):
                    print("You left the room.")
                    break
                logging.info("Received from " + str(main_context.tcpClientSocket) + " -> " + " ".join(message))
                if not message:
                    continue
                if message[0] == "JOINED":
                    print("User " + message[1] + " joined the room from " + str((message[2].split(":")[0], int(message[2].split(":")[1]))) + ".")
                    main_context.online_room_peers[message[1]] = (message[2].split(":")[0], int(message[2].split(":")[1]))
                    print(message[1] + " joined the room from " + str((message[2].split(":")[0], int(message[2].split(":")[1]))) + ".")
                elif message[0] == "LEFT":
                    if message[1] in main_context.online_room_peers:
                        del main_context.online_room_peers[message[1]]
                    print(message[1] + " left the room.")
            except OSError as oErr:
                logging.error("OSError: {0}".format(oErr))

    def handle_udp_chat_room(self, main_context):
        inputs = [main_context.udpClientSocket]
        while inputs and not self.stop:
            try:
                readable, writable, exceptional = select.select(inputs, [], [], 0.1)
            except:
                logging.error("UDP Client error")
                break
            for s in readable:
                if s is main_context.udpClientSocket:
                    try:
                        message, clientAddress = main_context.udpClientSocket.recvfrom(1024)
                    except:
                        logging.error("UDP Client error")
                        break
                    temp = message.decode().split()
                    username = temp[0]
                    message_content = " ".join(temp[1:])
                    if username not in main_context.online_room_peers:
                        main_context.online_room_peers[username] = clientAddress
                    print(username + ": " + message_content)

    def start_threads(self):
        self.roomTCPThread.start()
        self.roomUDPThread.start()

    def stop_threads(self):
        self.stop = True
        self.roomTCPThread.join()
        self.roomUDPThread.join()



def broadcast_message(main_context, message):
    for username, address in main_context.online_room_peers.items():
        main_context.udpClientSocket.sendto(str(main_context.loginCredentials[0] + " " + message).encode(), address)
