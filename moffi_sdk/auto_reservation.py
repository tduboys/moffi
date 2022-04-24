"""
Moffi auto reservation functions
"""

import logging
from datetime import datetime, timedelta

from moffi_sdk.reservations import get_reservations_by_date
from moffi_sdk.spaces import BUILDING_TIMEZONE, get_desk_for_date, get_workspace_details

MAX_DAYS = 30


def auto_reservation(desk: str, city: str, workspace: str, auth_token: str):
    """Auto reservation loop"""

    workspace_details = get_workspace_details(city=city, workspace=workspace, auth_token=auth_token)

    reservations = get_reservations_by_date(auth_token=auth_token)

    workspace_reservation_range_min = datetime.now(BUILDING_TIMEZONE) + timedelta(
        minutes=workspace_details.get("plageMini", {}).get("minutes", 0)
    )
    workspace_reservation_range_max = datetime.now(BUILDING_TIMEZONE) + timedelta(
        minutes=workspace_details.get("plageMaxi", {}).get("minutes", 0)
    )
    # set max range at end of day
    workspace_reservation_range_max = datetime.combine(
        workspace_reservation_range_max.date(), datetime.max.time(), tzinfo=workspace_reservation_range_max.tzinfo
    )

    workspace_closed_days = []
    for day, details in workspace_details.get("schedule", {}).items():
        if isinstance(details, dict) and details.get("isOpen") is not None:
            if not details.get("isOpen", True):
                workspace_closed_days.append(day.lower())

    if workspace_closed_days:
        logging.debug(f"Workspace closed days are {', '.join(workspace_closed_days)}")

    for delay in range(1, MAX_DAYS):
        future_date = datetime.now(BUILDING_TIMEZONE) + timedelta(days=delay)
        if len(reservations.get(future_date.date(), [])) > 0:
            logging.info(f"User already have a reservation for date {future_date.date().isoformat()}")
            for resa in reservations.get(future_date.date(), []):
                logging.info(str(resa))
        else:
            # test if out of range
            if workspace_reservation_range_min > future_date:
                logging.info(f"Date {future_date.date().isoformat()} is too close from now to reserve a desk")
                continue
            if future_date > workspace_reservation_range_max:
                logging.info(f"Date {future_date.date().isoformat()} is out of workspace range. Ending loop")
                break

            # test if office opened
            if future_date.strftime("%A").lower() in workspace_closed_days:
                logging.info(f"Workspace is closed on {future_date.strftime('%A')}")
                continue

            logging.info(f"No reservation for date {future_date.date().isoformat()}")
            desk_details = get_desk_for_date(
                desk_name=desk,
                building_id=workspace_details.get("building", {}).get("id"),
                workspace_id=workspace_details.get("id"),
                target_date=future_date,
                auth_token=auth_token,
                floor=workspace_details.get("floor", {}).get("level"),
            )
            logging.debug(desk_details)
