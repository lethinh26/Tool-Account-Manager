class AccountManagerException(Exception):
    def __init__(self, message: str, details: dict = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class AccountNotFoundException(AccountManagerException):
    pass


class AccountAlreadyExistsException(AccountManagerException):
    pass


class ProxyNotFoundException(AccountManagerException):
    pass


class ProxyConnectionException(AccountManagerException):
    pass


class BrowserException(AccountManagerException):
    pass


class BrowserNotFoundException(AccountManagerException):
    pass


class LoginDetectionException(AccountManagerException):
    pass


class ConfigurationException(AccountManagerException):
    pass


class FileOperationException(AccountManagerException):
    pass


class ValidationException(AccountManagerException):
    pass
