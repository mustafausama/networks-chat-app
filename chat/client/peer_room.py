from chat.common.utils import receiveTCPMessage
import logging
import select

def handle_tcp_chat_room(main_context, secret):
    inputs = [main_context.roomTCPSocket]
    client_socket, client_address = None, None
    while inputs:
        readable, writable, exceptional = select.select(inputs, [], [])
        for s in readable:
            if s is main_context.roomTCPSocket:
                try:
                    client_socket, client_address = main_context.roomTCPSocket.accept()
                except:
                    logging.error("TCP Client error")
                    break
                break
        if not client_socket:
            continue
        try:
            message = receiveTCPMessage(client_socket)
        except:
            logging.error("TCP Client error")
            break
        if message == secret:
            break

    while True:
        try:
            try:
                message = receiveTCPMessage(client_socket).split()
            except:
                logging.error("TCP Client error")
                break
            logging.info("Received from " + str(client_address) + " -> " + " ".join(message))
            if not message:
                continue
            if message[0] == "JOINED":
                main_context.online_room_peers[message[1]] = (message[2].split(":")[0], int(message[2].split(":")[1]))
                print(message[1] + " joined the room from " + str((message[2].split(":")[0], int(message[2].split(":")[1]))) + ".")
            elif message[0] == "LEFT":
                if message[1] in main_context.online_room_peers:
                    del main_context.online_room_peers[message[1]]
                print(message[1] + " left the room.")
        except OSError as oErr:
            logging.error("OSError: {0}".format(oErr))

def handle_udp_chat_room(main_context):
    inputs = [main_context.roomUDPSocket]
    while inputs:
        try:
            readable, writable, exceptional = select.select(inputs, [], [])
        except:
            logging.error("UDP Client error")
            break
        for s in readable:
            if s is main_context.roomUDPSocket:
                try:
                    message, clientAddress = main_context.roomUDPSocket.recvfrom(1024)
                except:
                    logging.error("UDP Client error")
                    break
                temp = message.decode().split()
                username = temp[0]
                message_content = " ".join(temp[1:])
                if username not in main_context.online_room_peers:
                    main_context.online_room_peers[username] = clientAddress
                print(username + ": " + message_content)

def broadcast_message(main_context, message):
    for username, address in main_context.online_room_peers.items():
        # print("Sending message to: " + username + " at " + str(address) + "...")
        main_context.roomUDPSocket.sendto(str(main_context.loginCredentials[0] + " " + message).encode(), address)
