"""
MOFFI Authentication
"""

from typing import Any, Dict
from urllib.parse import urlencode

import requests
from requests.structures import CaseInsensitiveDict

from moffi_sdk.exceptions import AuthenticationException, RequestException


class Session:
    """Moffi session auth"""

    token: str
    MOFFI_API = "https://api.moffi.io/api"

    def signin(self, username: str, password: str) -> Dict[str, Any]:
        """
        Authenticate to Moffi API and return all profile information

        Raise AuthenticationException in case of error
        """

        data = {"captcha": "NOT_PROVIDED", "email": username, "password": password}
        try:
            response = requests.post(url=f"{self.MOFFI_API}/signin", json=data)
        except requests.exceptions.RequestException as ex:
            raise AuthenticationException from ex

        if response.status_code != 200:
            raise AuthenticationException(f"Signing error {response.status_code} {response.text}")

        profile = response.json()
        self.token = profile.get("token")
        if not self.token:
            raise AuthenticationException("No token found on profile")
        return profile

    def query(  # pylint: disable=too-many-arguments
        self,
        method: str,
        url: str,
        params: Dict[str, str] = None,
        headers: Dict[str, str] = None,
        data: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """
        Query Moffi API

        :param method: Used method (GET, POST, OPTIONS…)
        :param url: Moffi endpoint URL
        :param headers: custom headers
        :param data: body data
        :return: Json response
        :raise: RequestException
        """

        if not url.startswith(self.MOFFI_API):
            if not url.startswith("/"):
                url = f"/{url}"
            url = f"{self.MOFFI_API}{url}"

        if params:
            url = f"{url}?{urlencode(params)}"

        ciheaders = CaseInsensitiveDict()
        if headers is not None:
            for key, value in headers.items():
                ciheaders[key] = value

        ciheaders["Accept"] = "application/json"
        if self.token:
            ciheaders["Authorization"] = f"Bearer {self.token}"

        if method.lower() not in requests.__dict__:
            raise RecursionError(f"Unknown method {method}")
        method = requests.__dict__[method.lower()]

        try:
            response = method(url=url, headers=ciheaders, json=data)
        except requests.exceptions.RequestException as ex:
            raise RequestException from ex

        response.raise_for_status()

        return response.json()


session = Session()
