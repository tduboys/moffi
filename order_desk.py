#!/usr/bin/env python3

"""
Order a desk in Moffi
Main program
"""

import sys

from moffi_sdk.auth import get_auth_token
from moffi_sdk.order import order_desk
from utils import (  # pylint: disable=R0801
    DEFAULT_CONFIG_RESERVATION_TEMPLATE,
    ConfigError,
    parse_config,
    setup_logging,
    setup_reservation_parser,
)

if __name__ == "__main__":

    PARSER = setup_reservation_parser()
    PARSER.add_argument("--date", "-t", help="Date to book")
    CONFIG_TEMPLATE = DEFAULT_CONFIG_RESERVATION_TEMPLATE
    CONFIG_TEMPLATE["date"] = {"mandatory": True}
    try:  # pylint: disable=R0801
        CONF = parse_config(argv=PARSER.parse_args(), config_template=CONFIG_TEMPLATE)
    except ConfigError as ex:
        PARSER.print_help()
        sys.stderr.write(f"\nerror: {str(ex)}\n")
        sys.exit(2)

    setup_logging(CONF)

    TOKEN = get_auth_token(username=CONF.get("user"), password=CONF.get("password"))
    order_desk(
        desk=CONF.get("desk"),
        city=CONF.get("city"),
        workspace=CONF.get("workspace"),
        order_date=CONF.get("date"),
        auth_token=TOKEN,
    )
