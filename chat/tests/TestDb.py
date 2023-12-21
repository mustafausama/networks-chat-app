import unittest
from chat.server.db import DB


class TestDB(unittest.TestCase):

    def setUp(self):
        self.db_instance = DB()

    def test_is_account_exist_existing_user(self):
        # Create a user named "tamer"
        username = "tamer"
        hashed_password = "example_hashed_password"
        salt = "example_salt"
        self.db_instance.register(username, hashed_password, salt)

        # Assert that the result matches the expected user data
        result = self.db_instance.is_account_exist(username)
        self.assertTrue(result)
        self.assertEqual(result["username"], username)

    def test_is_account_exist_nonexistent_user(self):

        # Assert that the result is None for a nonexistent user
        self.assertFalse(self.db_instance.is_account_exist("ahmed"))


if __name__ == '__main__':
    unittest.main()
