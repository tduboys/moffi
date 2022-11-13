"""
Moffi auto reservation functions
"""

import logging
from datetime import datetime, timedelta
from typing import List, Optional

from moffi_sdk.exceptions import OrderException
from moffi_sdk.order import order_desk_from_details
from moffi_sdk.reservations import get_reservations_by_date
from moffi_sdk.spaces import BUILDING_TIMEZONE, get_desk_for_date, get_workspace_details

MAX_DAYS = 30


def auto_reservation(  # pylint: disable=too-many-locals,too-many-branches,too-many-statements
    desk: str, city: str, workspace: str, work_days: Optional[List[int]] = None
):
    """Auto reservation loop"""

    if work_days is None:
        work_days = range(1, 7)

    workspace_details = get_workspace_details(city=city, workspace=workspace)

    reservations = get_reservations_by_date()

    workspace_reservation_range_min = datetime.now(BUILDING_TIMEZONE.get("tz")) + timedelta(
        minutes=workspace_details.get("plageMini", {}).get("minutes", 0)
    )
    workspace_reservation_range_max = datetime.now(BUILDING_TIMEZONE.get("tz")) + timedelta(
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
        future_date = datetime.now(BUILDING_TIMEZONE.get("tz")) + timedelta(days=delay)
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

            if int(future_date.strftime("%u")) not in work_days:
                logging.info(f"{future_date.strftime('%A')} is not on config working days")
                continue

            logging.info(f"No reservation for date {future_date.date().isoformat()}")
            desk_details = get_desk_for_date(
                desk_name=desk,
                building_id=workspace_details.get("building", {}).get("id"),
                workspace_id=workspace_details.get("id"),
                target_date=future_date.date(),
                floor=workspace_details.get("floor", {}).get("level"),
            )

            if desk_details.get("status") != "AVAILABLE":
                logging.warning(f"Desk {desk} is not available for reservation")
                continue

            logging.info(f"Order desk {desk} for date {future_date.date().isoformat()}")
            try:
                order_desk_from_details(
                    order_date=future_date.date(),
                    workspace_details=workspace_details,
                    desk_details=desk_details,
                )
                logging.info("Order successful")
            except OrderException as ex:
                logging.warning(f"Unable to order desk : {repr(ex)}")
                continue
