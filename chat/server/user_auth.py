import hashlib
import secrets
from chat.common.exceptions import UserExistsException, UserNotFoundException, IncorrectPasswordException
from chat.server.db import DB
db = DB()
class UserAuth:
    PEPPER = "pepperonipizza"
    
    @staticmethod
    def _hash_password(password, salt):
        # Hash the password using SHA-256 with salt and pepper
        hash_input = password + salt + UserAuth.PEPPER
        hashed_password = hashlib.sha256(hash_input.encode()).hexdigest()
        return hashed_password

    @staticmethod
    def register(username, password):
        # Check if the username is already registered
        if db.is_account_exist(username):
            raise UserExistsException("Username already exists.")

        # Generate a random salt
        salt = secrets.token_hex(16)

        # Hash the password with salt and pepper
        hashed_password = UserAuth._hash_password(password, salt)

        # Register the user
        db.register(username, hashed_password, salt)
    
    @staticmethod
    def login(username, password):
        # Check if the username exists
        user_data = db.is_account_exist(username)
        if user_data is None:
            raise UserNotFoundException("Username not found.")

        # Hash the entered password with the stored salt and pepper
        hashed_password = UserAuth._hash_password(password, user_data["salt"])

        # Check if the entered password matches the stored hashed password
        if hashed_password != user_data["hashed_password"]:
            raise IncorrectPasswordException("Incorrect password.")
