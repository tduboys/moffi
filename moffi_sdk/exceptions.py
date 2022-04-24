"""
All MOFFI SDK exceptions
"""


class MoffiSdkException(Exception):
    """Main Moffi SDK exception"""


class AuthenticationException(MoffiSdkException):
    """Error on Moffi authentication"""


class RequestException(MoffiSdkException):
    """Exception during request to Moffi API"""


class ItemNotFoundException(MoffiSdkException):
    """Item not found in Moffi API"""
