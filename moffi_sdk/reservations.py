"""
MOFFI reservations items
 """
import logging
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List

from dateutil import parser as dateparser

from moffi_sdk.exceptions import MoffiSdkException
from moffi_sdk.utils import query

AVAILABLE_STEPS = {
    "validation": "VALIDATION",
    "invitation": "INVITATION",
    "waiting": "WAITING",
    "inProgress": "IN_PROGRESS",
    "finished": "FINISHED",
}
AVAILABLE_STATUS = ["CREATED", "VALIDATED", "CONFIRMED", "PAID", "FINISHED", "CANCELLED"]


@dataclass
class ReservationItem:
    """Reservation item"""

    workspace_name: str
    workspace_address: str
    desk_name: str
    start: datetime
    end: datetime
    step: str
    status: str

    def __str__(self):
        return (
            f"{self.workspace_name} - {self.desk_name}"
            f" / status {self.status} / step {self.step}"
            f" / from {self.start.isoformat()} to {self.end.isoformat()}"
        )


def get_reservations(auth_token: str, steps: List[str] = None, view_cancelled: bool = True) -> List[ReservationItem]:
    """
    Get all reservations
    """

    reservations = []

    if not auth_token:
        raise MoffiSdkException("Missing token on get_reservations")

    if steps is None:
        steps = AVAILABLE_STEPS.keys()

    # count number of items
    counts = query(method="GET", url="/orders/count", auth_token=auth_token)

    for step in steps:
        if AVAILABLE_STEPS.get(step) is None or counts.get(step) is None:
            logging.warning(f"Unknown reservation step {step}, ignoring.")
            continue

        size = counts.get(step)
        if size == 0:
            logging.debug(f"No reservations on step {step}")
            continue

        params = {"step": AVAILABLE_STEPS.get(step), "kind": "BOOKING", "size": size, "page": 0}
        unparsed_reservations = query(method="GET", url="/orders", params=params, auth_token=auth_token)
        reservations += map_reservations(unparsed_reservations)

    if view_cancelled:
        if counts.get("cancelled") == 0:
            logging.debug("No reservations on state cancelled")
        else:
            params = {"status": "CANCELLED", "size": counts.get("cancelled"), "page": 0}
            unparsed_reservations = query(method="GET", url="/orders", params=params, auth_token=auth_token)
            reservations += map_reservations(unparsed_reservations)

    return reservations


def map_reservations(reservations: dict) -> List[ReservationItem]:
    """
    Map a list of reservations from API to list of ReservationItem
    """

    content = reservations.get("content", [])
    cleaned = []
    for reservation in content:
        step = reservation.get("step")
        status = reservation.get("status")

        for booking in reservation.get("bookings", []):
            workspace = booking.get("workspace", {}).get("title")
            address = booking.get("workspace", {}).get("address")
            start = dateparser.parse(booking.get("start"))
            end = dateparser.parse(booking.get("end"))

            for seat in booking.get("bookedSeats", []):
                item = ReservationItem(
                    workspace_name=workspace,
                    workspace_address=address,
                    desk_name=seat.get("seat", {}).get("fullname"),
                    start=start,
                    end=end,
                    step=step,
                    status=status,
                )
                cleaned.append(item)

    return cleaned


def get_reservations_by_date(
    auth_token: str, steps: List[str] = None, view_cancelled: bool = True
) -> Dict[str, List[ReservationItem]]:
    """
    Get all reservations in dict format, key is starting date, value are list of reservations for this date
    """

    reservations = get_reservations(auth_token=auth_token, steps=steps, view_cancelled=view_cancelled)

    ordered_reservations = defaultdict(list)

    for resa in reservations:
        ordered_reservations[resa.start.date()].append(resa)

    return ordered_reservations
