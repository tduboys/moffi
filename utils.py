"""
Utils functions for main programs
"""

import argparse
import logging
import os
from configparser import ConfigParser
from typing import Any, Dict, List

from dateutil import parser as dateparser

DEFAULT_CONFIG_RESERVATION_TEMPLATE = {
    "verbose": {"section": "Logging", "key": "Verbose", "mandatory": False, "default_value": False},
    "user": {"section": "Auth", "key": "User", "mandatory": True},
    "password": {"section": "Auth", "key": "Password", "mandatory": True},
    "city": {"section": "Reservation", "key": "City", "mandatory": True},
    "workspace": {"section": "Reservation", "key": "Workspace", "mandatory": True},
    "desk": {"section": "Reservation", "key": "Desk", "mandatory": True},
}


class ConfigError(Exception):
    """Configuration error"""


def parse_config(  # pylint: disable=too-many-branches
    argv: Any, config_template: Dict[str, List[str]]
) -> Dict[str, str]:
    """
    Parse given config and default config file
    Set mandatory keys from config_template
    """
    config_file = f"{os.environ.get('HOME')}/.config/moffi.ini"
    try:
        if argv.config:
            if os.path.exists(argv.config):
                config_file = argv.config
            else:
                logging.warning(f"Config file {config_file} not found, try default config file")
    except AttributeError:
        pass

    config_ini = ConfigParser()
    if os.path.exists(config_file):
        config_ini.read(config_file)

    config = {}

    # Reading config file and default values
    for ckey, settings in config_template.items():
        section = settings.get("section")
        fkey = settings.get("key")

        if section and section in config_ini.sections():
            if fkey and fkey in config_ini[section]:
                config[ckey] = config_ini[section][fkey]

        if ckey not in config and "default_value" in settings:
            config[ckey] = settings.get("default_value")

    # overwrite with argv
    for var in config_template:
        if var in argv.__dict__ and getattr(argv, var) is not None:
            config[var] = getattr(argv, var)  # pylint: disable=modified-iterating-dict

    # reformat config
    for ckey, settings in config_template.items():
        if settings.get("formatter") is not None and config.get(ckey) is not None:
            config[ckey] = settings["formatter"](config[ckey])

    # check mandatory config
    for ckey, settings in config_template.items():
        if settings.get("mandatory", False) and ckey not in config:
            raise ConfigError(f"Missing configuration value for {ckey}")

    return config


def setup_reservation_parser() -> argparse.ArgumentParser:
    """Setup Parser for reservation"""
    parser = argparse.ArgumentParser()
    parser.add_argument("--verbose", "-v", action="store_true", help="More verbose")
    parser.add_argument("--user", "-u", help="Moffi username")
    parser.add_argument("--password", "-p", help="Moffi password")
    parser.add_argument("--city", "-c", help="City to book")
    parser.add_argument("--workspace", "-w", help="Workspace to book")
    parser.add_argument("--desk", "-d", help="Desk to book")
    parser.add_argument("--config", help="Config file path")

    return parser


def setup_logging(conf: Dict[str, str]) -> None:
    """Setup logging"""
    if conf.get("verbose"):
        level = logging.DEBUG
    else:
        level = logging.INFO
    logging.basicConfig(level=level)


def format_working_days(conf: Any) -> List[int]:
    """Format working_days config to a valid config"""

    if isinstance(conf, list):
        conf_list = conf
    elif isinstance(conf, str):
        # test multiple separators
        if "," in conf:
            conf_list = conf.split(",")
        elif " " in conf:
            conf_list = conf.split()
        else:
            conf_list = [conf]
    else:
        logging.warning(f"Working days conf is unknown type {conf}")
        return []

    work_days = set()
    for item in conf_list:
        # test conf as int
        try:
            day = int(item)
            if -1 < day < 8:
                work_days.add(day)
                continue
            logging.warning(f"Ignoring working day {day}")
        except ValueError:
            pass

        # test conf as strftime date style
        try:
            fulldate = dateparser.parse(item)
            day = int(fulldate.strftime("%w"))
            work_days.add(day)
        except (dateparser.ParserError, ValueError):
            logging.warning(f"Ignoring unparseable day {item}")

    return list(work_days)
