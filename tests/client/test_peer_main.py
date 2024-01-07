import unittest
from unittest.mock import patch, call, MagicMock, Mock
from chat.client.peer_main import login, createAccount, inputUsername, inputRegAddress, inputPassword, PeerMain

class TestChatInputValidation(unittest.TestCase):
    # input functions testing
    @patch('chat.client.peer_main.print_colored_text')
    @patch('chat.client.peer_main.get_input', side_effect=['121', '127.0.1.1:3232'])
    def test_inputRegAddress(self, mock_get_input, mock_print):
        self.assertEqual(inputRegAddress("test"), ("127.0.1.1", 3232))
        mock_get_input.assert_has_calls([call(), call()])
        mock_print.assert_has_calls([call("test", "yellow"), call("Please enter a valid address formatted as (host:port): ", 'red')])
    
    @patch('chat.client.peer_main.get_input', side_effect=['', 'test'])
    def test_inputUsername(self, mock_get_input):
        self.assertEqual(inputUsername(), 'test')
        mock_get_input.assert_has_calls([call('Username: ', 'yellow'), call('Please enter a valid username: ', 'red')])

    @patch('getpass.getpass', side_effect=['', 'testpass'])
    def test_inputPassword(self, mock_getpass):
        self.assertEqual(inputPassword(), 'testpass')
        mock_getpass.assert_has_calls([call("Password: "), call("Password field must be filled: ")])

    # register testing
    @patch('chat.client.peer_main.receiveTCPMessage', return_value="join-success")
    @patch('chat.client.peer_main.sendTCPMessage', side_effect=lambda x, y: None)
    @patch('socket.socket')
    def test_register_success(self, mock_socket, mock_sendTCPMessage, mock_receiveTCPMessage):
        mock_socket_instance = mock_socket.return_value
        self.assertEqual(createAccount("test", "test", mock_socket_instance), "join-success")
        mock_sendTCPMessage.assert_called_once_with(mock_socket_instance, "JOIN test test")
        mock_receiveTCPMessage.assert_called()
    
    @patch('chat.client.peer_main.receiveTCPMessage', return_value="join-exist")
    @patch('chat.client.peer_main.sendTCPMessage', side_effect=lambda x, y: None)
    @patch('socket.socket')
    def test_register_account_exist(self, mock_socket, mock_sendTCPMessage, mock_receiveTCPMessage):
        mock_socket_instance = mock_socket.return_value
        self.assertEqual(createAccount("test", "test", mock_socket_instance), "join-exist")
        mock_sendTCPMessage.assert_called_once_with(mock_socket_instance, "JOIN test test")
        mock_receiveTCPMessage.assert_called()


    # login testing
    @patch('chat.client.peer_main.receiveTCPMessage', return_value="login-success 1234")
    @patch('chat.client.peer_main.sendTCPMessage', side_effect=lambda x, y: None)
    @patch('socket.socket')
    def test_login_success(self, mock_socket, mock_sendTCPMessage, mock_receiveTCPMessage):
        mock_socket_instance = mock_socket.return_value
        login("test", "test", 1234, mock_socket_instance)
        mock_sendTCPMessage.assert_called_once_with(mock_socket_instance, "LOGIN test test 1234")
        mock_receiveTCPMessage.assert_called()
    
    @patch('chat.client.peer_main.receiveTCPMessage', return_value="login-account-not-exist")
    @patch('chat.client.peer_main.sendTCPMessage', side_effect=lambda x, y: None)
    @patch('socket.socket')
    def test_login_account_not_exist(self, mock_socket, mock_sendTCPMessage, mock_receiveTCPMessage):
        mock_socket_instance = mock_socket.return_value
        login("test", "test", 1234, mock_socket_instance)
        mock_sendTCPMessage.assert_called_once_with(mock_socket_instance, "LOGIN test test 1234")
        mock_receiveTCPMessage.assert_called()

    @patch('chat.client.peer_main.receiveTCPMessage', return_value="login-online")
    @patch('chat.client.peer_main.sendTCPMessage', side_effect=lambda x, y: None)
    @patch('socket.socket')
    def test_login_online(self, mock_socket, mock_sendTCPMessage, mock_receiveTCPMessage):
        mock_socket_instance = mock_socket.return_value
        login("test", "test", 1234, mock_socket_instance)
        mock_sendTCPMessage.assert_called_once_with(mock_socket_instance, "LOGIN test test 1234")
        mock_receiveTCPMessage.assert_called()
    
    @patch('chat.client.peer_main.receiveTCPMessage', return_value="login-wrong-password")
    @patch('chat.client.peer_main.sendTCPMessage', side_effect=lambda x, y: None)
    @patch('socket.socket')
    def test_login_wrong_password(self, mock_socket, mock_sendTCPMessage, mock_receiveTCPMessage):
        mock_socket_instance = mock_socket.return_value
        login("test", "test", 1234, mock_socket_instance)
        mock_sendTCPMessage.assert_called_once_with(mock_socket_instance, "LOGIN test test 1234")
        mock_receiveTCPMessage.assert_called()
    
    @patch('chat.client.peer_main.receiveTCPMessage', return_value="login-wrong-password")
    @patch('chat.client.peer_main.sendTCPMessage', side_effect=lambda x, y: None)
    @patch('socket.socket')
    def test_login_wrong_password(self, mock_socket, mock_sendTCPMessage, mock_receiveTCPMessage):
        mock_socket_instance = mock_socket.return_value
        login("test", "test", 1234, mock_socket_instance)
        mock_sendTCPMessage.assert_called_once_with(mock_socket_instance, "LOGIN test test 1234")
        mock_receiveTCPMessage.assert_called()


class TestPeerMain(unittest.TestCase):
    @patch('chat.client.peer_main.inputRegAddress')
    @patch('chat.client.peer_main.socket')
    def setUp(self, mock_socket, mock_inputRegAddress):
        mock_socket.return_value = MagicMock()
        mock_inputRegAddress.return_value = ('127.0.0.1', 3232)

        self.peer_main = PeerMain()
        self.peer_main.timer = Mock()

    # Test mainLoop register choice
    @patch('chat.client.peer_main.createAccount')
    @patch('chat.client.peer_main.inputPassword', return_value=['password'])
    @patch('chat.client.peer_main.inputUsername', return_value=['username'])
    @patch('chat.client.peer_main.get_input', side_effect=['1', 'CANCEL'])
    def test_mainLoop_choice_1(self, mock_input, mock_inputUsername, mock_inputPassword, mock_createAccount):
        self.peer_main.print_coices_colored = Mock()
        self.peer_main.mainLoop()

        self.peer_main.print_coices_colored.assert_called()
        mock_input.assert_called()
        mock_inputUsername.assert_called()
        mock_inputPassword.assert_called()
        mock_createAccount.assert_called_once_with(['username'], ['password'], self.peer_main.tcpClientSocket)


    @patch('chat.client.peer_main.PeerServer')
    @patch('chat.client.peer_main.print_colored_text')
    @patch('chat.client.peer_main.login')
    @patch('chat.client.peer_main.find_available_port')
    @patch('chat.client.peer_main.get_hostname')
    @patch('chat.client.peer_main.inputPassword')
    @patch('chat.client.peer_main.inputUsername')
    @patch('chat.client.peer_main.get_input', side_effect=['2', 'CANCEL'])
    def test_mainLoop_choice_2(self, mock_input, mock_inputUsername, mock_inputPassword, mock_get_hostname, mock_find_available_port, mock_login, mock_print_colored_text, mock_PeerServer):
        mock_inputUsername.return_value = 'username'
        mock_inputPassword.return_value = 'password'
        mock_get_hostname.return_value = '127.0.0.1'
        mock_find_available_port.return_value = 1234
        mock_login.return_value = (1, 'payload')
        mock_PeerServer.return_value = MagicMock()
        mock_PeerServer.return_value.start = Mock()
        self.peer_main.sendHelloMessage = Mock()
        self.peer_main.isOnline = False
        self.peer_main.mainLoop()
        mock_inputUsername.assert_called()
        mock_inputPassword.assert_called()
        mock_get_hostname.assert_called()
        mock_find_available_port.assert_called()
        mock_login.assert_called_once_with('username', 'password', '127.0.0.1:1234', self.peer_main.tcpClientSocket)


    @patch('chat.client.peer_main.print_colored_text')
    @patch('chat.client.peer_main.get_input', side_effect=['3', 'CANCEL'])
    def test_mainLoop_choice_3(self, mock_input, mock_print_colored_text):
        self.peer_main.isOnline = True
        self.peer_main.logout = Mock()
        self.peer_main.tcpClientSocket = MagicMock()
        self.peer_main.peerServer = MagicMock()
        self.peer_main.peerServer.tcpServerSocket = MagicMock()
        self.peer_main.peerClient = MagicMock()
        self.peer_main.peerClient.tcpClientSocket = MagicMock()
        self.peer_main.peerClient.tcpClientSocket.close = Mock()
        self.peer_main.mainLoop()
        
        self.peer_main.logout.assert_called_once_with(1)
        self.peer_main.peerServer.tcpServerSocket.close.assert_called()
        self.peer_main.peerClient.tcpClientSocket.close.assert_called()
        mock_print_colored_text.assert_called_with("Logged out successfully", 'green')


    @patch('chat.client.peer_main.print_colored_text')
    @patch('chat.client.peer_main.get_input', side_effect=['3', 'CANCEL'])
    def test_mainLoop_choice_32(self, mock_input, mock_print_colored_text):
        self.peer_main.isOnline = False
        self.peer_main.logout = Mock()
        self.peer_main.mainLoop()
        self.peer_main.logout.assert_called_once_with(2)

    @patch('chat.client.peer_main.print_colored_text')
    @patch('chat.client.peer_main.inputUsername')
    @patch('chat.client.peer_main.get_input', side_effect=['5', 'n', 'CANCEL'])
    def test_mainLoop_choice_5(self, mock_input, mock_inputUsername, mock_print_colored_text):
        mock_inputUsername.return_value = 'username'
        self.peer_main.isOnline = True
        self.peer_main.searchUser = Mock(return_value=['1', '2'])
        self.peer_main.mainLoop()
        mock_inputUsername.assert_called()
        self.peer_main.searchUser.assert_called_once_with('username')

    @patch('chat.client.peer_main.print_colored_text')
    @patch('chat.client.peer_main.PeerClient')
    @patch('chat.client.peer_main.get_input', side_effect=['OK', 'CANCEL'])
    def test_mainLoop_choice_OK(self, mock_input, mock_PeerClient, mock_print_colored_text):
        self.peer_main.isOnline = True
        self.peer_main.loginCredentials = ['username']
        self.peer_main.peerServer = MagicMock()
        self.peer_main.peerServer.connectedPeerIP = '231.32.12.131'
        self.peer_main.peerServer.connectedPeerPort = 1234
        self.peer_main.mainLoop()
        mock_PeerClient.assert_called_once_with(self.peer_main.peerServer.connectedPeerIP, self.peer_main.peerServer.connectedPeerPort , self.peer_main.loginCredentials[0], self.peer_main.peerServer, "OK")
        mock_PeerClient.return_value.start.assert_called()
        mock_PeerClient.return_value.join.assert_called()

    @patch('chat.client.peer_main.print_colored_text')
    @patch('chat.client.peer_main.get_input', side_effect=['REJECT', 'CANCEL'])
    def test_mainLoop_choice_REJECT(self, mock_input, mock_print_colored_text):
        self.peer_main.isOnline = True
        self.peer_main.peerServer = MagicMock()
        self.peer_main.peerServer.connectedPeerIP = '122.12.12.12'
        self.peer_main.peerServer.connectedPeerSocket = MagicMock()
        self.peer_main.mainLoop()
        self.peer_main.peerServer.connectedPeerSocket.send.assert_called_once_with("REJECT".encode())
        self.peer_main.peerServer.isChatRequested = 0


    @patch('chat.client.peer_main.print_colored_text')
    @patch('chat.client.peer_main.get_input', side_effect=['6', 'room_name', 'CANCEL'])
    def test_mainLoop_choice_6(self, mock_input, mock_print_colored_text):
        self.peer_main.isOnline = True
        self.peer_main.isInChatRoom = False
        self.peer_main.tcpClientSocket = MagicMock()
        self.peer_main.tcpClientSocket.send = Mock()
        self.peer_main.tcpClientSocket.recv.return_value = "room-created".encode()
        self.peer_main.mainLoop()
        self.peer_main.tcpClientSocket.send.assert_called_once_with("CREATE-ROOM room_name".encode())


    @patch('chat.client.peer_main.print_colored_text')
    @patch('chat.client.peer_main.get_input', side_effect=['7', 'CANCEL'])
    def test_mainLoop_choice_7(self, mock_input, mock_print_colored_text):
        self.peer_main.isOnline = True
        self.peer_main.tcpClientSocket = MagicMock()
        self.peer_main.tcpClientSocket.send = Mock()
        self.peer_main.tcpClientSocket.recv.return_value = "list-rooms room1 room2 room3".encode()
        self.peer_main.mainLoop()
        self.peer_main.tcpClientSocket.send.assert_called_once_with("LIST-ROOMS".encode())
        mock_print_colored_text.assert_has_calls([call("Chat rooms:", 'green'), call("room1", 'cyan'), call("room2", 'cyan'), call("room3", 'cyan')])


    @patch('chat.client.peer_main.PeerRoom')
    @patch('chat.client.peer_main.print_colored_text')
    @patch('chat.client.peer_main.get_input', side_effect=['8', 'room_name', ':q', 'CANCEL'])
    def test_mainLoop_choice_8(self, mock_input, mock_print_colored_text, mock_PeerRoom):
        self.peer_main.isOnline = True
        self.peer_main.isInChatRoom = False
        self.peer_main.tcpClientSocket = MagicMock()
        self.peer_main.tcpClientSocket.send = Mock()
        mock_PeerRoom.return_value = MagicMock()
        self.peer_main.tcpClientSocket.recv.return_value = "room-joined user1:120.1.2.1:1234 user2:123.12.2.1:1234".encode()
        
        self.peer_main.mainLoop()
        self.peer_main.tcpClientSocket.send.assert_called_with("LEAVE-ROOM room_name".encode())
        self.assertEqual(self.peer_main.isInChatRoom, False)



if __name__ == '__main__':
    unittest.main()
