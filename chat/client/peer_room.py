from chat.common.utils import receiveTCPMessage, print_colored_text, format_text
import logging
import select
import threading

class PeerRoom:
    def __init__(self, main_context):
        self.stop = False
        self.roomThread = threading.Thread(target=self.handle_room, args=(main_context,))

    def handle_room(self, main_context):
        inputs = [main_context.tcpClientSocket, main_context.udpClientSocket]
        while inputs and not self.stop:
            try:
                readable, writable, exceptional = select.select(inputs, [], [], 0.01)
            except:
                logging.error("Client error")
                break
            for s in readable:
                if s is main_context.tcpClientSocket:
                    try:
                        message = receiveTCPMessage(main_context.tcpClientSocket).split()
                    except:
                        logging.error("TCP Client error")
                        break
                    if not message or len(message) == 0: continue
                    if(message[0] == 'room-left'):
                        print_colored_text("You left the room.", 'red')
                        break
                    logging.info("Received from " + str(main_context.tcpClientSocket) + " -> " + " ".join(message))
                    if not message:
                        continue
                    if message[0] == "JOINED":
                        print_colored_text(message[1] + " joined the room from " + str((message[2].split(":")[0], int(message[2].split(":")[1]))) + ".", 'green')
                        main_context.online_room_peers[message[1]] = (message[2].split(":")[0], int(message[2].split(":")[1]))
                    elif message[0] == "LEFT":
                        if message[1] in main_context.online_room_peers:
                            del main_context.online_room_peers[message[1]]
                        print_colored_text(message[1] + " left the room.", 'yellow')
                elif s is main_context.udpClientSocket:
                    try:
                        message, clientAddress = main_context.udpClientSocket.recvfrom(1024)
                    except:
                        logging.error("UDP Client error")
                        break
                    temp = message.decode().split()
                    if not temp or len(temp) == 0: continue
                    username = temp[0]
                    message_content = " ".join(temp[1:])
                    if username not in main_context.online_room_peers:
                        main_context.online_room_peers[username] = clientAddress
                    print_colored_text(username + ': ', 'cyan', end='')
                    print(format_text(message_content))

    def start_thread(self):
        self.roomThread.start()

    def stop_thread(self):
        self.stop = True
        self.roomThread.join()

def broadcast_message(main_context, message):
    for username, address in main_context.online_room_peers.items():
        main_context.udpClientSocket.sendto(str(main_context.loginCredentials[0] + " " + message).encode(), address)
