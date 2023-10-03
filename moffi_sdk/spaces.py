"""
Moffi Space details

Get details about buildings, workspaces, desks
"""

from datetime import date, datetime, timedelta
from typing import Any, Dict

import pytz
from rfc3339 import rfc3339

from moffi_sdk.exceptions import ItemNotFoundException
from moffi_sdk.utils import query

BUILDING_TIMEZONE = {"tz": pytz.timezone("UTC")}


def get_building(name: str, auth_token: str) -> Dict[str, Any]:
    """Get details about building"""

    # list cities available
    available_buildings = query(
        method="get", url="/users/buildings", params={"withDetails": False}, auth_token=auth_token
    )
    city = None
    for building in available_buildings:
        if building.get("name") == name:
            city = building
            break

    if city is None:
        buildings = [building.get("name", "NO_NAME") for building in available_buildings]
        raise ItemNotFoundException(f"City {name} not found", available_items=buildings)

    building_details = query(method="GET", url=f"/buildings/{city.get('id')}", auth_token=auth_token)
    BUILDING_TIMEZONE["tz"] = pytz.timezone(building_details.get("timezone", "UTC"))

    return building_details


def get_workspace_availabilities(
    name: str, auth_token: str, city: str = None, building_details: Dict[str, Any] = None, target_date: datetime = None
) -> Dict[str, Any]:
    """Get details about workspace"""

    if building_details is None:
        building_details = get_building(name=city, auth_token=auth_token)

    # iterate on floors to find workspace
    workspace_details = None
    if target_date is None:
        target_date = rfc3339(datetime.now(BUILDING_TIMEZONE.get("tz")) + timedelta(days=1))

    workspace_names = []
    for floor in building_details.get("floors", []):
        params = {
            "buildingId": building_details.get("id"),
            "startDate": target_date,
            "endDate": target_date,
            "places": 1,
            "period": "DAY",
            "floor": floor.get("level"),
        }
        floor_details = query(
            method="get",
            url="/workspaces/availabilities",
            params=params,
            auth_token=auth_token,
        )
        workspace_names.extend([wks.get("workspace", {}).get("title", "NO_NAME") for wks in floor_details])
        for workspace in floor_details:
            if workspace.get("workspace", {}).get("title", "") == name:
                workspace_details = workspace
                break
        if workspace_details is not None:
            break
        

    if workspace_details is None:
        # failed to find workspace
        raise ItemNotFoundException(f"Workspace {name} not found", available_items=workspace_names)

    return workspace_details


def get_desk_details_from_workspace(name: str, workspace_details: Dict[str, Any]) -> Dict[str, Any]:
    """Get details about desk"""

    desk_details = None
    for seat in workspace_details.get("seats", []):
        if seat.get("seat", {}).get("fullname") == name:
            desk_details = seat
            break
    if desk_details is None:
        desks = [seat.get("seat", {}).get("fullname", "NO_NAME") for seat in workspace_details.get("seats", [])]
        raise ItemNotFoundException(f"Desk {name} not found", available_items=desks)

    return desk_details


def get_desk_for_date(  # pylint: disable=too-many-arguments
    desk_name: str, building_id: str, workspace_id: str, floor: int, target_date: date, auth_token: str
) -> Dict[str, Any]:
    """Get desk availabilities for a given date"""

    params = {
        "buildingId": building_id,
        "places": 1,
        "period": "DAY",
        "floor": floor,
        "workspaceId": workspace_id,
        "startDate": rfc3339(datetime.combine(target_date, datetime.min.time())),
        "endDate": rfc3339(datetime.combine(target_date, datetime.max.time())),
    }
    workspace_details_list = query(method="GET", url="/workspaces/availabilities", params=params, auth_token=auth_token)
    if not workspace_details_list:
        workspaces = [workspace.get("workspace", {}).get("id", "NO_NAME") for workspace in workspace_details_list]
        raise ItemNotFoundException(
            f"Workspace id {workspace_id} not found on building {building_id}", available_items=workspaces
        )
    workspace_details = workspace_details_list[0]

    desk_details = get_desk_details_from_workspace(name=desk_name, workspace_details=workspace_details)

    return desk_details


def get_workspace_details(city: str, workspace: str, auth_token: str) -> Dict[str, Any]:
    """Get all workspace details"""

    building_details = get_building(name=city, auth_token=auth_token)
    workspace_availabilities = get_workspace_availabilities(
        name=workspace, building_details=building_details, auth_token=auth_token
    )

    # https://api.moffi.io/api/workspaces/url/coworking/418608-Paris-23-personnes
    workspace_details = query(
        method="GET",
        url=f"/workspaces/url/{workspace_availabilities.get('workspace', {}).get('url')}",
        auth_token=auth_token,
    )

    return workspace_details
