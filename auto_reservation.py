#!/usr/bin/env python3

"""
Moffi Auto-reservation main program
"""

from moffi_sdk.auth import get_auth_token
from moffi_sdk.auto_reservation import auto_reservation
from utils import DEFAULT_CONFIG_RESERVATION_TEMPLATE, parse_config, setup_logging, setup_reservation_parser

if __name__ == "__main__":

    PARSER = setup_reservation_parser()
    PARSER.add_argument("--workingdays", nargs="+", help="Days on week to book", type=int, required=False)
    CONFIG_TEMPLATE = DEFAULT_CONFIG_RESERVATION_TEMPLATE
    CONFIG_TEMPLATE["workingdays"] = {
        "section": "Reservation",
        "key": "Working Days",
        "mandatory": False,
        "default_value": None,
    }
    CONF = parse_config(argv=PARSER.parse_args(), config_template=CONFIG_TEMPLATE)
    setup_logging(CONF)

    TOKEN = get_auth_token(username=CONF.get("user"), password=CONF.get("password"))
    auto_reservation(
        desk=CONF.get("desk"),
        city=CONF.get("city"),
        workspace=CONF.get("workspace"),
        auth_token=TOKEN,
        work_days=CONF.get("workingdays"),
    )
