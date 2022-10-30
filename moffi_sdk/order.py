"""
Moffi orders
"""
import logging
from datetime import date, datetime, time, timezone
from typing import Any, Dict

from rfc3339 import rfc3339

from moffi_sdk.exceptions import OrderException, RequestException, UnavailableException
from moffi_sdk.spaces import BUILDING_TIMEZONE, get_desk_for_date, get_workspace_details
from moffi_sdk.utils import query


def order_desk_from_details(  # pylint: disable=too-many-locals
    order_date: date, workspace_details: Dict[str, Any], desk_details: Dict[str, Any], auth_token: str
) -> Dict[str, Any]:
    """
    Order a desk in a workspace

    :param order_date: date to order
    :param workspace_details: json with all details of workspace (see moffi_sdk.spaces.get_workspace_details)
    :param desk_details: json with all details of desk (see moffi_sdk.spaces.get_desk_for_date)
    :param auth_token: API token
    :return: paid order
    :raise: OrderException if error during order
    """
    # verify unavailabilities for user
    params = {
        "companyId": workspace_details.get("company", {}).get("id"),
        "start": rfc3339(datetime.combine(order_date, datetime.min.time())),
        "end": rfc3339(datetime.combine(order_date, datetime.max.time())),
    }
    unavailabilities = query(method="GET", url="/planning/unavailabilities", params=params, auth_token=auth_token)
    if unavailabilities.get(order_date.isoformat(), {}).get("date") == order_date.isoformat():
        raise UnavailableException(f"Orders is unavailable on {order_date.isoformat()}")

    # looking for schedule for the day
    day_name = order_date.strftime("%A").lower()
    schedule = workspace_details.get("schedule", {})
    if schedule.get(day_name) is None or not schedule.get(day_name, {}).get("isOpen", False):
        raise UnavailableException(f"Date {order_date.isoformat()} is not opened for reservation for this workspace")

    # compute starting date and ending date
    open_time_str = schedule.get(day_name, {}).get("beginningMorning", "00:00")
    close_time_str = schedule.get(day_name, {}).get("endingAfternoon", "23:59")

    try:
        open_time = time(hour=int(open_time_str.split(":")[0]), minute=int(open_time_str.split(":")[1]), second=0)
        start_date = datetime.combine(date=order_date, time=open_time, tzinfo=BUILDING_TIMEZONE.get("tz")).astimezone(
            timezone.utc
        )
    except ValueError:
        open_time = time(hour=0, minute=0, second=0)
        start_date = datetime.combine(date=order_date, time=open_time, tzinfo=timezone.utc)
    try:
        close_time = time(hour=int(close_time_str.split(":")[0]), minute=int(close_time_str.split(":")[1]), second=0)
        end_date = datetime.combine(date=order_date, time=close_time, tzinfo=BUILDING_TIMEZONE.get("tz")).astimezone(
            timezone.utc
        )
    except ValueError:
        close_time = time(hour=23, minute=59, second=59)
        end_date = datetime.combine(date=order_date, time=close_time, tzinfo=timezone.utc)

    # create estimate
    body_estimate = {
        "id": workspace_details.get("id"),
        "workspaceId": workspace_details.get("id"),
        "start": rfc3339(start_date, utc=True),
        "end": rfc3339(end_date, utc=True),
        "isMonthlyBooking": False,
        "places": 1,
        "days": [{"day": order_date.isoformat(), "date": rfc3339(start_date, utc=True), "period": "DAY"}],
        "bookedSeats": [{"seat": desk_details.get("seat")}],
        "period": "DAY",
        "rrule": None,
    }
    estimate = query(method="POST", url="/bookings/estimate", data=body_estimate, auth_token=auth_token)

    # verify desk is available on estimate
    desk_fullname = desk_details.get("seat", {}).get("fullname")
    if estimate.get("errorCode"):
        raise UnavailableException(
            f"Error during estimate for desk {desk_fullname} on {order_date.isoformat()} : {estimate.get('errorCode')}"
        )

    # create order
    body_order = {
        "company": {"id": workspace_details.get("company", {}).get("id")},
        "timezone": str(BUILDING_TIMEZONE.get("tz")),
        "coupon": None,
        "bookings": [
            {
                "id": None,
                "workspace": {
                    "id": workspace_details.get("id"),
                },
                "workspaceId": workspace_details.get("id"),
                "start": rfc3339(start_date, utc=True),
                "end": rfc3339(start_date, utc=True),
                "places": 1,
                "isMonthlyBooking": False,
                "coupon": None,
                "period": "DAY",
                "bookedSeats": [{"seat": desk_details.get("seat")}],
                "days": [{"day": order_date.isoformat(), "date": rfc3339(start_date, utc=True), "period": "DAY"}],
                "bookNextToInfo": {"id": None},
                "rrule": None,
            }
        ],
        "origin": "WIDGET",
    }
    order = query(method="POST", url="/orders/add", data=body_order, auth_token=auth_token)

    # verify price is 0
    try:
        price = int(order.get("totalBookings", -1))
        if price != 0:
            raise OrderException(f"Price for desk {desk_fullname} is {price}, we also work on free orders")
    except ValueError:
        logging.warning(f"Unable to check price on order {order.get('totalBookings')}")

    order_id = order.get("id")
    if not order_id:
        raise OrderException("Unable to find order id in generated order")

    # pay order
    body_pay = {
        "orderId": order_id,
        "customer": {"id": order.get("author", {}).get("id")},
        "method": "FREE",
        "methodId": None,
        "target": {"kind": "ORDER", "order": order},
    }
    paid_order = query(method="POST", url=f"/orders/{order_id}/pay", data=body_pay, auth_token=auth_token)

    if paid_order.get("status") != "PAID":
        OrderException(f"Paid order is not on status PAID : {paid_order.get('status')}")

    return paid_order


def order_desk(city: str, workspace: str, desk: str, order_date: str, auth_token: str) -> Dict[str, Any]:
    """
    Order a desk from basic details

    :param city: City where Workspace is located
    :param workspace: Workspace where order a desk
    :param desk: Desk fullname to order
    :param order_date: date in isoformat to book
    :param auth
    :return: Completed order
    :raise: OrderException in case of error
    """
    try:
        target_date = date.fromisoformat(order_date)
    except ValueError as ex:
        raise OrderException from ex

    try:
        workspace_details = get_workspace_details(city=city, workspace=workspace, auth_token=auth_token)
        desk_details = get_desk_for_date(
            desk_name=desk,
            building_id=workspace_details.get("building", {}).get("id"),
            workspace_id=workspace_details.get("id"),
            target_date=target_date,
            auth_token=auth_token,
            floor=workspace_details.get("floor", {}).get("level"),
        )
    except RequestException as ex:
        raise OrderException from ex

    if desk_details.get("status") != "AVAILABLE":
        raise UnavailableException(f"Desk {desk} is not available for reservation")

    logging.info(f"Order desk {desk} for date {order_date}")
    order_details = order_desk_from_details(
        order_date=target_date,
        workspace_details=workspace_details,
        desk_details=desk_details,
        auth_token=auth_token,
    )
    logging.info("Order successful")
    return order_details
