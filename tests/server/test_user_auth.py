import unittest
import hashlib
from unittest.mock import patch, MagicMock
from chat.server.user_auth import UserAuth, UserExistsException, UserNotFoundException, IncorrectPasswordException

def hash_password_helper(password, salt, pepper):
    hash_input = password + salt + pepper
    hashed_password = hashlib.sha256(hash_input.encode()).hexdigest()
    return hashed_password

class TestUserAuth(unittest.TestCase):

    @patch('chat.server.user_auth.secrets.token_hex', return_value="1234567890123456")
    @patch('chat.server.user_auth.db')
    def test_register_new_user(self, mock_db, _):
        mock_db.is_account_exist.return_value = None
        mock_db.register.return_value = MagicMock()
        password, salt = "password123", "1234567890123456"
        UserAuth.register("new_user", password)
        mock_db.is_account_exist.assert_called_once_with("new_user")
        mock_db.register.assert_called_once_with("new_user", hash_password_helper(password, salt, UserAuth.PEPPER), salt)

    @patch('chat.server.user_auth.secrets.token_hex', return_value="1234567890123456")
    @patch('chat.server.user_auth.db')
    def test_register_existing_user(self, mock_db, _):
        mock_db.is_account_exist.return_value = MagicMock()
        with self.assertRaises(UserExistsException):
            UserAuth.register("existing_user", "password123")
        mock_db.is_account_exist.assert_called_once_with("existing_user")
        mock_db.register.assert_not_called()

    @patch('chat.server.user_auth.db')
    def test_login_correct_password(self, mock_db):
        password, salt = "password123", "1234567890123456"
        mock_db.is_account_exist.return_value = {
            "username": "test_user",
            "hashed_password": hash_password_helper(password, salt, UserAuth.PEPPER),
            "salt": salt
        }
        UserAuth.login("test_user", password)
        mock_db.is_account_exist.assert_called_once_with("test_user")

    @patch('chat.server.user_auth.db')
    def test_login_nonexistent_user(self, mock_db):
        mock_db.is_account_exist.return_value = None
        with self.assertRaises(UserNotFoundException):
            UserAuth.login("nonexistent_user", "password123")
        mock_db.is_account_exist.assert_called_once_with("nonexistent_user")

    @patch('chat.server.user_auth.db')
    def test_login_incorrect_password(self, mock_db):
        password, salt = "password123", "1234567890123456"
        mock_db.is_account_exist.return_value = {
            "username": "test_user",
            "hashed_password": hash_password_helper(password, salt, UserAuth.PEPPER),
            "salt": salt
        }
        with self.assertRaises(IncorrectPasswordException):
            UserAuth.login("test_user", "wrong_password")
        mock_db.is_account_exist.assert_called_once_with("test_user")

if __name__ == '__main__':
    unittest.main()
