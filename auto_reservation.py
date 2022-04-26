#!/usr/bin/env python3

"""
Moffi Auto-reservation main program
"""

from moffi_sdk.auth import get_auth_token
from moffi_sdk.auto_reservation import auto_reservation
from utils import parse_config, setup_logging, setup_reservation_parser

if __name__ == "__main__":

    PARSER = setup_reservation_parser()
    CONFIG_TEMPLATE = {
        "Logging": ["Verbose"],
        "Auth": ["User", "Password"],
        "Reservation": ["City", "Workspace", "Desk"],
    }
    CONF = parse_config(argv=PARSER.parse_args(), config_template=CONFIG_TEMPLATE)
    setup_logging(CONF)

    TOKEN = get_auth_token(username=CONF.get("user"), password=CONF.get("password"))
    auto_reservation(desk=CONF.get("desk"), city=CONF.get("city"), workspace=CONF.get("workspace"), auth_token=TOKEN)
