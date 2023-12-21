import unittest
from unittest.mock import patch, MagicMock
from chat.server.db import DB 

class TestDBMethods(unittest.TestCase):
    def setUp(self):
        self.mock_mongo_client = MagicMock()
        self.db = DB()
        self.db.client = self.mock_mongo_client
        self.db.db = self.mock_mongo_client['database']

    @patch('chat.server.db.MongoClient')
    def test_is_account_exist_true(self, _):
        self.db.db.accounts.find.return_value = [{"username": "test_user"}]
        result = self.db.is_account_exist("test_user")
        self.assertTrue(result)

    @patch('chat.server.db.MongoClient')
    def test_is_account_exist_false(self, _):
        data = {
            "username": "test_user",
            "hashed_password": "test_hashed_password",
            "salt": "test_salt"
        }
        self.db.db.accounts.find.return_value = data
        result = self.db.is_account_exist("test_user")
        self.assertFalse(result == data)

    @patch('chat.server.db.MongoClient')
    def test_register(self, _):
        self.db.db.accounts.insert_one.return_value = "test_inserted"
        result = self.db.register("test_user", "test_hashed_password")
        self.assertEqual(result, "test_inserted")

if __name__ == '__main__':
    unittest.main()
