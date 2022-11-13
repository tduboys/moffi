#!/usr/bin/env python3

"""
Moffi Auto-reservation main program
"""
import sys

from moffi_sdk.auth import session
from moffi_sdk.auto_reservation import auto_reservation
from utils import (  # pylint: disable=R0801
    DEFAULT_CONFIG_RESERVATION_TEMPLATE,
    ConfigError,
    parse_config,
    setup_logging,
    setup_reservation_parser,
    format_working_days,
)

if __name__ == "__main__":

    PARSER = setup_reservation_parser()
    PARSER.add_argument("--workingdays", nargs="+", help="Days on week to book", required=False)
    CONFIG_TEMPLATE = DEFAULT_CONFIG_RESERVATION_TEMPLATE
    CONFIG_TEMPLATE["workingdays"] = {
        "section": "Reservation",
        "key": "Working Days",
        "mandatory": False,
        "default_value": None,
        "formatter": format_working_days,
    }
    try:  # pylint: disable=R0801
        CONF = parse_config(argv=PARSER.parse_args(), config_template=CONFIG_TEMPLATE)
    except ConfigError as ex:
        PARSER.print_help()
        sys.stderr.write(f"\nerror: {str(ex)}\n")
        sys.exit(2)
    setup_logging(CONF)

    session.signin(username=CONF.get("user"), password=CONF.get("password"))
    auto_reservation(
        desk=CONF.get("desk"),
        city=CONF.get("city"),
        workspace=CONF.get("workspace"),
        work_days=CONF.get("workingdays"),
    )
