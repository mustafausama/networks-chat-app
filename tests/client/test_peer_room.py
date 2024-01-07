from chat.client.peer_room import PeerRoom, broadcast_message
from chat.client.peer_main import PeerMain
from unittest.mock import patch, MagicMock
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
        # self.assertIsInstance(self.peer_room.roomTCPThread, MagicMock)
        # self.assertIsInstance(self.peer_room.roomUDPThread, MagicMock)
        self.assertIsInstance(self.peer_room.roomThread, MagicMock)

    @patch('chat.client.peer_room.select.select')
    @patch('chat.client.peer_room.print_colored_text')
    def test_handle_room(self, mock_print, mock_select):
        self.main_context.tcpClientSocket = MagicMock()
        self.main_context.udpClientSocket = MagicMock()
        mock_select.side_effect = [[[self.main_context.tcpClientSocket, self.main_context.udpClientSocket], [], []], [[], None, None]]
        self.main_context.tcpClientSocket.recv.return_value = 'JOINED user1 127.0.0.1:1234'.encode()
        self.peer_room.handle_room(self.main_context)
        mock_print.assert_called_once_with("user1 joined the room from ('127.0.0.1', 1234).", 'green')
    
    # test broadcast_message
    @patch('chat.client.peer_room.print_colored_text')
    def test_broadcast_message(self, mock_print):
        self.main_context.online_room_peers = {'user1': ('127.0.0.1', 1234)}
        self.main_context.udpClientSocket = MagicMock()
        self.main_context.loginCredentials = ['user2', 'password']
        broadcast_message(self.main_context, 'message')
        self.main_context.udpClientSocket.sendto.assert_called_once_with('user2 message'.encode(), ('127.0.0.1', 1234))

if __name__ == '__main__':
    unittest.main()
