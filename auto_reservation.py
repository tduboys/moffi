"""
Main
"""
import argparse
import logging

from moffi_sdk.auth import get_auth_token
from moffi_sdk.auto_reservation import auto_reservation

if __name__ == "__main__":

    PARSER = argparse.ArgumentParser()
    PARSER.add_argument("--verbose", "-v", action="store_true", help="More verbose")
    PARSER.add_argument("--user", "-u", help="Moffi username", required=True)
    PARSER.add_argument("--password", "-p", help="Moffi password", required=True)
    PARSER.add_argument("--city", "-c", help="City to book", required=True)
    PARSER.add_argument("--workspace", "-w", help="Workspace to book", required=True)
    PARSER.add_argument("--desk", "-d", help="Desk to book", required=True)
    ARGS = PARSER.parse_args()

    if ARGS.verbose:
        LEVEL = logging.DEBUG
    else:
        LEVEL = logging.INFO
    logging.basicConfig(level=LEVEL)

    TOKEN = get_auth_token(username=ARGS.user, password=ARGS.password)

    auto_reservation(desk=ARGS.desk, city=ARGS.city, workspace=ARGS.workspace, auth_token=TOKEN)
