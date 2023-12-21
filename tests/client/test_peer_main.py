import unittest
from unittest.mock import patch, call
from chat.client.peer_main import login, createAccount, inputPortNumber, inputPassword, inputUsername, inputRegAddress

class TestChatInputValidation(unittest.TestCase):
    # input functions testing
    @patch('builtins.print')
    @patch('chat.client.peer_main.get_input', side_effect=['121', '127.0.1.1:3232'])
    def test_inputRegAddress(self, mock_get_input, mock_print):
        self.assertEqual(inputRegAddress("test"), ("127.0.1.1", 3232))
        mock_get_input.assert_has_calls([call(), call()])
        mock_print.assert_has_calls([call("test"), call("Please enter a valid address formatted as (host:port): ")])
    
    @patch('chat.client.peer_main.get_input', side_effect=['', 'test'])
    def test_inputUsername(self, mock_get_input):
        self.assertEqual(inputUsername(), 'test')
        mock_get_input.assert_has_calls([call("Username: "), call("Please enter a valid username: ")])
    
    @patch('chat.client.peer_main.get_input', side_effect=['123456', '1234'])
    def test_inputPortNumber(self, mock_get_input):
        self.assertEqual(inputPortNumber(), 1234)
        mock_get_input.assert_has_calls([call("Enter a port number for peer server: "), call("Please enter a valid port number: ")])

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

if __name__ == '__main__':
    unittest.main()
