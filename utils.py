"""
Utils functions for main programs
"""

import argparse
import logging
import os
from configparser import ConfigParser
from typing import Any, Dict, List


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

    config = {"verbose": False}

    # Reading config file
    for section, keys in config_template.items():
        if section in config_ini.sections():
            for key in keys:
                config[key.lower()] = config_ini[section].get(key)
        else:
            for key in keys:
                config[key.lower()] = None

    # overwrite with argv
    for var in config:
        if var in argv.__dict__ and getattr(argv, var) is not None:
            config[var] = getattr(argv, var)  # pylint: disable=modified-iterating-dict

    # check no config is None
    for key, value in config.items():
        if value is None:
            raise ConfigError(f"Missing configuration value for {key}")

    return config


def setup_reservation_parser() -> argparse.ArgumentParser:
    """Setup Parser for reservation"""
    parser = argparse.ArgumentParser()
    parser.add_argument("--verbose", "-v", action="store_true", help="More verbose", required=False)
    parser.add_argument("--user", "-u", help="Moffi username", required=False)
    parser.add_argument("--password", "-p", help="Moffi password", required=False)
    parser.add_argument("--city", "-c", help="City to book", required=False)
    parser.add_argument("--workspace", "-w", help="Workspace to book", required=False)
    parser.add_argument("--desk", "-d", help="Desk to book", required=False)
    parser.add_argument("--config", help="Config file path", required=False)

    return parser


def setup_logging(conf: Dict[str, str]) -> None:
    """Setup logging"""
    if conf.get("verbose"):
        level = logging.DEBUG
    else:
        level = logging.INFO
    logging.basicConfig(level=level)
