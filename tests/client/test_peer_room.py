from chat.client.peer_room import PeerRoom, broadcast_message
from chat.client.peer_main import PeerMain
from unittest.mock import patch, MagicMock, call
import unittest

class TestPeerRoom(unittest.TestCase):

    @patch('chat.client.peer_room.threading.Thread')
    def setUp(self, mock_thread):
        self.main_context = MagicMock(spec=PeerMain)
        self.main_context.online_room_peers = {}
        mock_thread.return_value = MagicMock()
        self.peer_room = PeerRoom(self.main_context)

    @patch('chat.client.peer_room.threading.Thread')
    def test_init(self, mock_thread):
        mock_thread.return_value = MagicMock()
        self.assertIsInstance(self.peer_room.roomTCPThread, MagicMock)
        self.assertIsInstance(self.peer_room.roomUDPThread, MagicMock)


    @patch('chat.client.peer_room.receiveTCPMessage', side_effect=['JOINED user1 127.0.0.1:1234', 'room-left'])
    @patch('chat.client.peer_room.print_colored_text')
    def test_handle_tcp_chat_room(self, mock_print, mock_receiveTCPMessage):
        self.main_context.tcpClientSocket = MagicMock()
        self.peer_room.handle_tcp_chat_room(self.main_context)
        mock_receiveTCPMessage.assert_any_call(self.main_context.tcpClientSocket)
        mock_print.assert_has_calls([call("user1 joined the room from ('127.0.0.1', 1234).", 'green'), call('You left the room.', 'red')])

    @patch('chat.client.peer_room.select.select')
    @patch('chat.client.peer_room.print_colored_text')
    def test_handle_udp_chat_room(self, mock_print, mock_select):
        self.main_context.udpClientSocket = MagicMock()
        mock_select.side_effect = [[[self.main_context.udpClientSocket], [], []], [[], None, None]]
        self.main_context.udpClientSocket.recvfrom.return_value = ('user1 hello world'.encode(), ('127.0.0.1', 1234))
        self.peer_room.handle_udp_chat_room(self.main_context)
        mock_print.assert_called_once_with('user1: ', 'cyan', end='')

if __name__ == '__main__':
    unittest.main()
