#!/usr/bin/env python3

"""
MOFFIcs

Reads reservations from moffi.io API
Return as ICS datas
"""

import argparse
import base64
import json
import sys
from datetime import date

import requests
from Crypto.Cipher import AES
from dateutil import parser as dateparser
from flask import Flask, Response, abort, make_response, request
from ics import Calendar, Event
from requests.structures import CaseInsensitiveDict

APP = Flask(__name__)

MOFFI_API = "https://api.moffi.io/api"

def encrypt(message: str, key: bytes) -> str:
    """
    Encrypt a message with AES256
    Return as base64 urlsafe string
    """
    cipher = AES.new(key, AES.MODE_EAX)
    ciphertext, tag = cipher.encrypt_and_digest(message.encode('utf-8'))

    nonce = base64.b64encode(cipher.nonce).decode('utf-8')
    tag = base64.b64encode(tag).decode('utf-8')
    ciphertext = base64.b64encode(ciphertext).decode('utf-8')
    datas = {"nonce": nonce, "tag": tag, "ciphertext": ciphertext}
    bdata = base64.urlsafe_b64encode(json.dumps(datas).encode('utf-8')).rstrip(b'=')
    return bdata.decode('utf-8')


def decrypt(message: str, key: bytes) -> str:
    """
    Decrypt a base64 urlsafe encrypted AES256 message
    """
    bmsg = message.encode('utf-8')
    padding = b'=' * (4 - (len(bmsg) % 4))
    datas = json.loads(base64.urlsafe_b64decode(bmsg + padding))
    nonce = base64.b64decode(datas.get('nonce'))
    tag = base64.b64decode(datas.get('tag'))
    ciphertext = base64.b64decode(datas.get('ciphertext'))
    cipher = AES.new(key, AES.MODE_EAX, nonce)
    return cipher.decrypt_and_verify(ciphertext, tag).decode('utf-8')


def signin(username: str, password: str) -> dict:
    """
    Authenticate to Moffi API and return all profile informations
    """

    data = {"captcha": "NOT_PROVIDED", "email": username, "password": password}
    response = requests.post(url=f"{MOFFI_API}/signin", json=data)

    if response.status_code != 200:
        APP.logger.warning(f"Signing error {response.status_code} {response.text}")
        abort(response.status_code, response.text)

    return response.json()


def get_reservations(token: str) -> list:
    """
    Get all future reservations
    """
    headers = CaseInsensitiveDict()
    headers["Accept"] = "application/json"
    headers["Authorization"] = f"Bearer {token}"

    # count number of items
    url = f"{MOFFI_API}/orders/count"
    response = requests.get(url=url, headers=headers)
    if response.status_code != 200:
        APP.logger.warning(f"Count reservations error {response.status_code} {response.text}")
        abort(response.status_code, response.text)

    counts = response.json()
    waiting = counts.get("waiting")
    in_progress = counts.get("inProgress")
    APP.logger.debug(f"Waiting events : {waiting}")
    APP.logger.debug(f"InProgress events : {in_progress}")

    reservations = []

    if waiting:
        url = f"{MOFFI_API}/orders?step=WAITING&kind=BOOKING&size={waiting}&page=0"
        response = requests.get(url=url, headers=headers)
        if response.status_code != 200:
            APP.logger.warning(f"Get waiting reservations error {response.status_code} {response.text}")
            abort(response.status_code, response.text)

        reservations += sanitize_reservations(response.json())

    if in_progress:
        url = f"{MOFFI_API}/orders?step=IN_PROGRESS&kind=BOOKING&size={in_progress}&page=0"
        response = requests.get(url=url, headers=headers)
        if response.status_code != 200:
            APP.logger.warning(f"Get waiting reservations error {response.status_code} {response.text}")
            abort(response.status_code, response.text)

        reservations += sanitize_reservations(response.json())

    APP.logger.debug(f"{len(reservations)} desks booked")
    return reservations


def sanitize_reservations(reservations: dict) -> list:
    """
    Sanitize Reservations dict
    to a more readable list
    """
    content = reservations.get("content", [])
    if len(content) != reservations.get("totalElements", 0):
        abort(500, "reservation content miss some items")

    cleaned = []
    for reservation in content:
        if reservation.get("type") != "BOOKING":
            continue
        if reservation.get("status") != "PAID":
            continue

        for booking in reservation.get("bookings", []):
            try:
                workspace = booking.get("workspace", {}).get("title", "Missing workspace name")
                address = booking.get("workspace", {}).get("address")
                start = dateparser.parse(booking.get("start"))
                end = dateparser.parse(booking.get("end"))

                if end.date() < date.today():
                    # skipping ended bookings
                    continue

                for seat in booking.get("bookedSeats", []):
                    item = {
                        "workspace": workspace,
                        "address": address,
                        "desk": seat.get("seat", {}).get("fullname", "Missing desk name"),
                        "reservationStart": start,
                        "reservationEnd": end,
                    }
                    cleaned.append(item)
            except Exception as ex:
                APP.logger.warning(f"Unable to parse booking {booking} : {repr(ex)}")

    return cleaned


def generate_calendar(events: list) -> Calendar:
    """
    Generate an ICS Calendar from a list of events
    """
    cal = Calendar()
    for item in events:
        event = Event()
        event.name = f"{item.get('workspace')} - {item.get('desk')}"
        event.begin = item.get("reservationStart")
        event.end = item.get("reservationEnd")
        event.location = item.get("address")
        cal.events.add(event)

    return cal


def get_ics_from_moffi(token: str) -> Response:
    """
    Get all reservations from moffi
    Return a flask responce object
    """
    if not token:
        abort(500, "missing token in user profile")

    reservations = get_reservations(token=token)

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
        abort(403, "missing basicauth")
    APP.logger.debug(f"Login : {auth.username}")

    user_profile = signin(username=auth.username, password=auth.password)
    token = user_profile.get("token")

    return get_ics_from_moffi(token=token)

@APP.route("/getToken")
def get_token():
    """
    Generate a token to use in /token route
    """
    if not APP.config.get('secret_key'):
        abort(500, "missing secret key in conf")

    auth = request.authorization
    if not auth:
        abort(403, "missing basicauth")
    APP.logger.debug(f"Login : {auth.username}")

    # ensure auth is legitimate
    signin(username=auth.username, password=auth.password)
    
    message = json.dumps({"login": auth.username, "password": auth.password})
    token = encrypt(message, APP.config.get('secret_key'))
    return {"token": token}

@APP.route("/token/<string:token>")
def get_with_token(token: str):
    """
    Main call with token authentication
    """
    if not APP.config.get('secret_key'):
        abort(500, "missing secret key in conf")
    authent = decrypt(token, APP.config.get('secret_key'))
    jauth = json.loads(authent)
    APP.logger.debug(f"Login : {jauth.get('login')}")

    user_profile = signin(username=jauth.get('login'), password=jauth.get('password'))
    moffi_token = user_profile.get("token")

    return get_ics_from_moffi(token=moffi_token)

if __name__ == "__main__":

    PARSER = argparse.ArgumentParser()
    PARSER.add_argument("--verbose", "-v", action="store_true", help="More verbose")
    PARSER.add_argument("--listen", "-l", help="Listen address (default to 0.0.0.0)", default="0.0.0.0")
    PARSER.add_argument("--port", "-p", help="Listen port (default to 8888)", default="8888")
    PARSER.add_argument("--secret", "-s", help="Secret key for token auth")
    ARGS = PARSER.parse_args()

    if ARGS.secret and len(ARGS.secret) not in [16, 24, 32]:
        APP.logger.error("Secret key must be 16, 24 or 32 chars long")
        sys.exit(1)

    APP.config['secret_key'] = ARGS.secret.encode("utf-8")

    APP.run(host=ARGS.listen, port=ARGS.port, debug=ARGS.verbose)
