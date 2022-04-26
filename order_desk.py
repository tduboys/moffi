#!/usr/bin/env python3

"""
Order a desk in Moffi
Main program
"""

from moffi_sdk.auth import get_auth_token
from moffi_sdk.order import order_desk
from utils import DEFAULT_CONFIG_RESERVATION_TEMPLATE, parse_config, setup_logging, setup_reservation_parser

if __name__ == "__main__":

    PARSER = setup_reservation_parser()
    PARSER.add_argument("--date", "-t", help="Date to book")
    CONFIG_TEMPLATE = DEFAULT_CONFIG_RESERVATION_TEMPLATE
    CONFIG_TEMPLATE["order_date"] = {"mandatory": True}
    CONF = parse_config(argv=PARSER.parse_args(), config_template=CONFIG_TEMPLATE)
    setup_logging(CONF)

    TOKEN = get_auth_token(username=CONF.get("user"), password=CONF.get("password"))
    order_desk(
        desk=CONF.get("desk"),
        city=CONF.get("city"),
        workspace=CONF.get("workspace"),
        order_date=CONF.get("order_date"),
        auth_token=TOKEN,
    )
