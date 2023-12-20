class UserExistsException(Exception):
    pass

class UserNotFoundException(Exception):
    pass

class IncorrectPasswordException(Exception):
    pass
class EmptyUsernameException(Exception):
    pass
class WeakPasswordException(Exception):
    pass