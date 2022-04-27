#!/usr/bin/env python3

"""
MOFFIcs

Reads reservations from moffi.io API
Return as ICS datas
"""

import argparse
import base64
import json
import random
import string
import sys
from typing import List

from Crypto.Cipher import AES
from flask import Flask, Response, abort, make_response, request
from ics import Calendar, Event

from moffi_sdk.auth import get_auth_token, signin
from moffi_sdk.reservations import ReservationItem, get_reservations
from utils import parse_config

APP = Flask(__name__)

MOFFI_API = "https://api.moffi.io/api"


def encrypt(message: str, key: bytes) -> str:
    """
    Encrypt a message with AES256
    Return as base64 urlsafe string
    """
    cipher = AES.new(key, AES.MODE_EAX)
    ciphertext, tag = cipher.encrypt_and_digest(message.encode("utf-8"))

    nonce = base64.b64encode(cipher.nonce).decode("utf-8")
    tag = base64.b64encode(tag).decode("utf-8")
    ciphertext = base64.b64encode(ciphertext).decode("utf-8")
    datas = {"nonce": nonce, "tag": tag, "ciphertext": ciphertext}
    bdata = base64.urlsafe_b64encode(json.dumps(datas).encode("utf-8")).rstrip(b"=")
    return bdata.decode("utf-8")


def decrypt(message: str, key: bytes) -> str:
    """
    Decrypt a base64 urlsafe encrypted AES256 message
    """
    bmsg = message.encode("utf-8")
    padding = b"=" * (4 - (len(bmsg) % 4))
    datas = json.loads(base64.urlsafe_b64decode(bmsg + padding))
    nonce = base64.b64decode(datas.get("nonce"))
    tag = base64.b64decode(datas.get("tag"))
    ciphertext = base64.b64decode(datas.get("ciphertext"))
    cipher = AES.new(key, AES.MODE_EAX, nonce)
    return cipher.decrypt_and_verify(ciphertext, tag).decode("utf-8")


def generate_calendar(events: List[ReservationItem]) -> Calendar:
    """
    Generate an ICS Calendar from a list of events
    """
    cal = Calendar()
    for item in events:
        event = Event()
        event.name = f"{item.workspace_name} - {item.desk_name}"
        event.begin = item.start.isoformat()
        event.end = item.end.isoformat()
        event.location = item.workspace_address
        cal.events.add(event)

    return cal


def get_ics_from_moffi(token: str) -> Response:
    """
    Get all reservations from moffi
    Return a flask responce object
    """
    if not token:
        abort(500, "missing token in user profile")

    reservations = get_reservations(auth_token=token, view_cancelled=False, steps=["waiting", "inProgress"])

    calendar = generate_calendar(reservations)
    response = make_response(str(calendar), 200)
    response.mimetype = "text/html"
    return response


@APP.route("/")
def get_with_basicauth():
    """
    Main call with basic authentication
    """
    auth = request.authorization
    if not auth:
        abort(401, "missing authentication")
    APP.logger.debug(f"Login : {auth.username}")  # pylint: disable=no-member

    token = get_auth_token(username=auth.username, password=auth.password)

    return get_ics_from_moffi(token=token)


@APP.route("/getToken")
def generate_token():
    """
    Generate a token to use in /token route
    """
    if not APP.config.get("secret_key"):
        abort(500, "missing secret key in conf")

    auth = request.authorization
    if not auth:
        abort(401, "missing authentication")
    APP.logger.debug(f"Login : {auth.username}")  # pylint: disable=no-member

    # ensure auth is legitimate
    signin(username=auth.username, password=auth.password)

    message = json.dumps({"login": auth.username, "password": auth.password})
    token = encrypt(message, APP.config.get("secret_key"))
    return {"token": token}


@APP.route("/token/<string:token>")
def get_with_token(token: str):
    """
    Main call with token authentication
    """
    if not APP.config.get("secret_key"):
        abort(500, "missing secret key in conf")
    authent = decrypt(token, APP.config.get("secret_key"))
    jauth = json.loads(authent)
    APP.logger.debug(f"Login : {jauth.get('login')}")  # pylint: disable=no-member

    moffi_token = get_auth_token(username=jauth.get("login"), password=jauth.get("password"))

    return get_ics_from_moffi(token=moffi_token)


if __name__ == "__main__":

    DEFAULT_SECRET = "".join(random.choice(string.ascii_letters) for x in range(32))

    PARSER = argparse.ArgumentParser()
    PARSER.add_argument("--verbose", "-v", action="store_true", help="More verbose")
    PARSER.add_argument("--listen", "-l", help="Listen address (default to 0.0.0.0)", default="0.0.0.0")
    PARSER.add_argument("--port", "-p", help="Listen port (default to 8888)", default="8888")
    PARSER.add_argument("--secret", "-s", help="Secret key for token auth", default=DEFAULT_SECRET)
    PARSER.add_argument("--config", help="Config file")
    ARGS = PARSER.parse_args()
    CONFIG_TEMPLATE = {"Logging": ["Verbose"], "Moffics": ["Secret"]}
    CONF = parse_config(argv=ARGS, config_template=CONFIG_TEMPLATE)

    if CONF.get("secret"):
        if len(CONF.get("secret")) not in [16, 24, 32]:
            APP.logger.error("Secret key must be 16, 24 or 32 chars long")
            sys.exit(1)
        APP.config["secret_key"] = CONF.get("secret").encode("utf-8")

    APP.run(host=ARGS.listen, port=ARGS.port, debug=ARGS.verbose)
