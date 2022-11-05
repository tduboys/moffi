"""
All MOFFI SDK exceptions
"""
from typing import List


class MoffiSdkException(Exception):
    """Main Moffi SDK exception"""


class AuthenticationException(MoffiSdkException):
    """Error on Moffi authentication"""


class RequestException(MoffiSdkException):
    """Exception during request to Moffi API"""


class ItemNotFoundException(MoffiSdkException):
    """Item not found in Moffi API"""

    def __init__(self, *args, available_items: List[str] = None, **kwargs):
        super().__init__(*args, **kwargs)
        self.available_items = available_items

    def __str__(self):
        str_e = super().__str__()
        if self.available_items:
            return f"{str_e}. Available items are {self.available_items}"
        return str_e


class OrderException(MoffiSdkException):
    """Error during order in Moffi API"""


class UnavailableException(OrderException):
    """Item is unavailable in Moffi API"""
