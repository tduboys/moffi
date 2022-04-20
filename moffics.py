#!/usr/bin/env python3

"""
MOFFIcs

Reads reservations from moffi.io API
Return as ICS datas
"""

import argparse

import requests
from datetime import date
from dateutil import parser as dateparser
from flask import Flask, abort, make_response, request
from ics import Calendar, Event
from requests.structures import CaseInsensitiveDict

APP = Flask(__name__)

MOFFI_API = "https://api.moffi.io/api"


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
        event.begin = item.get('reservationStart')
        event.end = item.get('reservationEnd')
        event.location = item.get('address')
        cal.events.add(event)

    return cal


@APP.route('/')
def get_ics_from_moffi():
    auth = request.authorization
    if not auth:
        abort(403, "missing basicauth")
    APP.logger.debug(f"Login : {auth.username}")

    user_profile = signin(username=auth.username, password=auth.password)
    token = user_profile.get("token")
    if not token:
        abort(500, "missing token in user profile")

    reservations = get_reservations(token=token)

    calendar = generate_calendar(reservations)
    response = make_response(str(calendar), 200)
    response.mimetype = 'text/html'
    return response


if __name__ == "__main__":

    PARSER = argparse.ArgumentParser()
    PARSER.add_argument("--verbose", "-v", action="store_true", help="More verbose")
    ARGS = PARSER.parse_args()

    APP.run(host="0.0.0.0", port="8888", debug=ARGS.verbose)
