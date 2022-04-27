#!/usr/bin/env python3

"""
Order a desk in Moffi
Main program
"""

from moffi_sdk.auth import get_auth_token
from moffi_sdk.order import order_desk
from utils import parse_config, setup_logging, setup_reservation_parser

if __name__ == "__main__":

    PARSER = setup_reservation_parser()
    PARSER.add_argument("--date", "-t", help="Date to book", required=True)
    ARGS = PARSER.parse_args()
    CONFIG_TEMPLATE = {
        "Logging": ["Verbose"],
        "Auth": ["User", "Password"],
        "Reservation": ["City", "Workspace", "Desk", "Date"],
    }
    CONF = parse_config(argv=ARGS, config_template=CONFIG_TEMPLATE)
    setup_logging(CONF)

    TOKEN = get_auth_token(username=CONF.get("user"), password=CONF.get("password"))
    order_desk(
        desk=CONF.get("desk"),
        city=CONF.get("city"),
        workspace=CONF.get("workspace"),
        order_date=ARGS.date,
        auth_token=TOKEN,
    )
