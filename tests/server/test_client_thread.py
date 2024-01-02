import unittest
from unittest.mock import patch, call, MagicMock, Mock
from chat.server.client_thread import ClientThread
unittest.TestLoader.sortTestMethodsUsing = None

class TestClientThread(unittest.TestCase):

    @patch('builtins.print')
    def setUp(self, mock_print):
        self.tcpClientSocket = MagicMock()
        self.server_context = MagicMock()

        self.ip = '127.0.0.1'
        self.port = 1234
        self.client_thread = ClientThread(self.ip, self.port, self.tcpClientSocket, self.server_context)
    
    @patch('builtins.print')
    @patch('chat.server.client_thread.threading.Lock')
    @patch('chat.server.client_thread.receiveTCPMessage')
    @patch('chat.server.client_thread.sendTCPMessage')
    @patch('chat.server.client_thread.UserAuth.register')
    def test_run_join_success(self, mock_register, mock_sendTCPMessage, mock_receiveTCPMessage, mock_lock, mock_print):
        mock_receiveTCPMessage.side_effect = ['JOIN test_user test_password', Exception()]
        mock_register.return_value = None
        self.client_thread.run()
        mock_sendTCPMessage.assert_called_once_with(self.tcpClientSocket, 'join-success')
    
    @patch('builtins.print')
    @patch('chat.server.client_thread.threading.Lock')
    @patch('chat.server.client_thread.receiveTCPMessage')
    @patch('chat.server.client_thread.sendTCPMessage')
    @patch('chat.server.client_thread.UserAuth.login')
    @patch('chat.server.client_thread.generate_random_secret', return_value='test_token')
    def test_run_login_online(self, mock_gen, mock_login, mock_sendTCPMessage, mock_receiveTCPMessage, mock_lock, mock_print):
        mock_receiveTCPMessage.side_effect = ['LOGIN test_user test_password 12122', Exception()]
        mock_login.return_value = None
        self.client_thread.server_context.tcpThreads = {'test_user': 'test_thread'}
        self.client_thread.run()
        mock_sendTCPMessage.assert_called_once_with(self.tcpClientSocket, 'login-online')

    @patch('builtins.print')
    @patch('chat.server.client_thread.threading.Lock')
    @patch('chat.server.client_thread.receiveTCPMessage')
    @patch('chat.server.client_thread.sendTCPMessage')
    def test_run_list_users(self, mock_sendTCPMessage, mock_receiveTCPMessage, mock_lock, mock_print):
        mock_receiveTCPMessage.side_effect = ['LIST-USERS', Exception()]
        self.client_thread.server_context.tcpThreads = {'test_user': 'test_thread'}
        self.client_thread.run()
        mock_sendTCPMessage.assert_called_once_with(self.tcpClientSocket, 'list-users test_user')
    
    @patch('builtins.print')
    @patch('chat.server.client_thread.threading.Lock')
    @patch('chat.server.client_thread.receiveTCPMessage')
    @patch('chat.server.client_thread.sendTCPMessage')
    @patch('chat.server.client_thread.UserAuth.fine_user')
    def test_run_search_user_not_found(self, mock_fine_user, mock_sendTCPMessage, mock_receiveTCPMessage, mock_lock, mock_print):
        mock_receiveTCPMessage.side_effect = ['SEARCH test_user', Exception()]
        mock_fine_user.return_value = False
        self.client_thread.run()
        mock_sendTCPMessage.assert_called_once_with(self.tcpClientSocket, 'search-user-not-found')

    @patch('builtins.print')
    @patch('chat.server.client_thread.threading.Lock')
    @patch('chat.server.client_thread.receiveTCPMessage')
    @patch('chat.server.client_thread.sendTCPMessage')
    def test_run_create_room(self, mock_sendTCPMessage, mock_receiveTCPMessage, mock_lock, mock_print):
        mock_receiveTCPMessage.side_effect = ['CREATE-ROOM test_room', Exception()]
        self.client_thread.server_context.chatRooms = {}
        self.client_thread.run()
        mock_sendTCPMessage.assert_called_once_with(self.tcpClientSocket, 'room-created')

    @patch('builtins.print')
    @patch('chat.server.client_thread.threading.Lock')
    @patch('chat.server.client_thread.receiveTCPMessage')
    @patch('chat.server.client_thread.sendTCPMessage')
    def test_run_list_rooms(self, mock_sendTCPMessage, mock_receiveTCPMessage, mock_lock, mock_print):
        mock_receiveTCPMessage.side_effect = ['LIST-ROOMS', Exception()]
        self.client_thread.server_context.chatRooms = {'test_room': 'test_thread'}
        self.client_thread.run()
        mock_sendTCPMessage.assert_called_once_with(self.tcpClientSocket, 'list-rooms test_room')
    
    @patch('builtins.print')
    @patch('chat.server.client_thread.threading.Lock')
    @patch('chat.server.client_thread.receiveTCPMessage')
    @patch('chat.server.client_thread.sendTCPMessage')
    def test_run_join_room(self, mock_sendTCPMessage, mock_receiveTCPMessage, mock_lock, mock_print):
        mock_receiveTCPMessage.side_effect = ['JOIN-ROOM test_room', Exception()]
        self.client_thread.server_context.chatRooms = {}
        self.client_thread.run()
        mock_sendTCPMessage.assert_called_once_with(self.tcpClientSocket, 'room-not-found')
    
    @patch('builtins.print')
    @patch('chat.server.client_thread.threading.Lock')
    @patch('chat.server.client_thread.receiveTCPMessage')
    @patch('chat.server.client_thread.sendTCPMessage')
    def test_run_leave_room(self, mock_sendTCPMessage, mock_receiveTCPMessage, mock_lock, mock_print):
        mock_receiveTCPMessage.side_effect = ['LEAVE-ROOM test_room', Exception()]
        self.client_thread.server_context.chatRooms = {'test_room': {'test_user': 'test_thread'}}
        self.client_thread.online_in_rooms = {'test_room'}
        self.client_thread.username = 'test_user'
        self.client_thread.run()
        mock_sendTCPMessage.assert_called_once_with(self.tcpClientSocket, 'room-left test_room')

if __name__ == '__main__':
    unittest.main()
