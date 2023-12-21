import unittest
from unittest.mock import patch
from chat.common.utils import find_available_port, sendTCPMessage, receiveTCPMessage, get_input

class TestUtils(unittest.TestCase):
    def test_find_available_port(self):
        # Ensure the find_available_port function returns a valid port
        port = find_available_port("localhost", 5000, 6000)
        self.assertTrue(5000 <= port < 6000)

    @patch('socket.socket')
    def test_send_receive_TCP_message(self, mock_socket):
        # Mocking the socket for testing send and receive functions

        # Test sendTCPMessage
        mock_socket_instance = mock_socket.return_value
        send_message = "Test message"
        sendTCPMessage(mock_socket_instance, send_message)
        mock_socket_instance.send.assert_called_once_with(send_message.encode())

        # Test receiveTCPMessage
        receive_message = "Received message"
        mock_socket_instance.recv.return_value.decode.return_value = receive_message
        result = receiveTCPMessage(mock_socket_instance)
        mock_socket_instance.recv.assert_called_once_with(1024)
        self.assertEqual(result, receive_message)

    @patch('builtins.input', return_value='test_input')
    def test_get_input(self, mock_input):
        # Test get_input function with mocked input
        result = get_input()
        mock_input.assert_called_once()
        self.assertEqual(result, 'test_input')

if __name__ == '__main__':
    unittest.main()
