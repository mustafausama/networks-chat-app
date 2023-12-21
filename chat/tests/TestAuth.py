import unittest
from chat.server.user_auth import *
from chat.common.exceptions import UserExistsException


class TestDB(unittest.TestCase):

    def setUp(self):
        # Create a new instance of the DB class for each test
        self.db_instance = DB()

    def test_register_existing_user(self):
        # Create a user named "tamer"
        username = "tamer"
        hashed_password = "example_hashed_password"
        self.db_instance.register(username, hashed_password)

        # Test that trying to register an existing user raises UserExistsException
        with self.assertRaises(UserExistsException):
            UserAuth.register(username, hashed_password)

    def test_register_non_existing_user(self):
        # Register the user
        result = UserAuth.register("hameedo","walahy123")

        # Assert that the registration was successful
        self.assertIsNotNone(result)


if __name__ == '__main__':
    unittest.main()
