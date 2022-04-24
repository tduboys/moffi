"""
MOFFI Utils methods
"""
from typing import Any, Dict
from urllib.parse import urlencode

import requests
from requests.structures import CaseInsensitiveDict

from moffi_sdk.exceptions import RequestException

MOFFI_API = "https://api.moffi.io/api"


def query(  # pylint: disable=too-many-arguments
    method: str,
    url: str,
    auth_token: str,
    params: Dict[str, str] = None,
    headers: Dict[str, str] = None,
    data: Dict[str, Any] = None,
) -> Dict[str, Any]:
    """
    Query Moffi API

    :param method: Used method (GET, POST, OPTIONS…)
    :param url: Moffi endpoint URL
    :param auth_token: Authentication token
    :param headers: custom headers
    :param data: body data
    :return: Json response
    :raise: RequestException
    """

    if not url.startswith(MOFFI_API):
        if not url.startswith("/"):
            url = f"/{url}"
        url = f"{MOFFI_API}{url}"

    if params:
        url = f"{url}?{urlencode(params)}"

    ciheaders = CaseInsensitiveDict()
    if headers is not None:
        for key, value in headers.items():
            ciheaders[key] = value

    ciheaders["Accept"] = "application/json"
    ciheaders["Authorization"] = f"Bearer {auth_token}"

    if method.lower() not in requests.__dict__:
        raise RecursionError(f"Unknown method {method}")
    method = requests.__dict__[method.lower()]

    try:
        result = method(url=url, headers=ciheaders, data=data)
    except requests.exceptions.RequestException as ex:
        raise RequestException from ex

    if result.status_code > 399:
        raise RequestException(f"Request error {result.status_code} {result.text}")

    return result.json()
