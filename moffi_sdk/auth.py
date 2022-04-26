"""
MOFFI Authentication
"""

from typing import Any, Dict

import requests

from moffi_sdk.exceptions import AuthenticationException
from moffi_sdk.utils import MOFFI_API


def signin(username: str, password: str) -> Dict[str, Any]:
    """
    Authenticate to Moffi API and return all profile informations

    Raise AuthenticationException in case of error
    """

    data = {"captcha": "NOT_PROVIDED", "email": username, "password": password}
    try:
        response = requests.post(url=f"{MOFFI_API}/signin", json=data)
    except requests.exceptions.RequestException as ex:
        raise AuthenticationException from ex

    if response.status_code != 200:
        raise AuthenticationException(f"Signing error {response.status_code} {response.text}")

    return response.json()


def get_auth_token(username: str, password: str) -> str:
    """
    Authenticate to Moffi API and return API authentication token

    Raise AuthenticationException in case of error
    """

    profile = signin(username=username, password=password)
    auth_token = profile.get("token")

    if not auth_token:
        raise AuthenticationException("No token found on profile")

    return auth_token
