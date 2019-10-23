"""Utility functions."""

import os
import socket

import structlog
from six.moves.configparser import ConfigParser

CONFIG_FILE = os.path.expanduser(os.path.join("~", ".config", "sublime", "setup.cfg"))
LOGGER = structlog.get_logger()

DEFAULT_CONFIG = {"api_key": ""}


def load_config():
    """Load configuration.

    :returns:
        Current configuration based on configuration file and environment variables.
    :rtype: dict

    """
    config_parser = ConfigParser(
        {key: str(value) for key, value in DEFAULT_CONFIG.items()}
    )
    config_parser.add_section("sublime")

    if os.path.isfile(CONFIG_FILE):
        LOGGER.debug("Parsing configuration file: %s...", CONFIG_FILE, path=CONFIG_FILE)
        with open(CONFIG_FILE) as config_file:
            config_parser.readfp(config_file)
    else:
        LOGGER.warning(
            "Configuration file not found: %s", CONFIG_FILE, path=CONFIG_FILE
        )

    if "SUBLIME_API_KEY" in os.environ:
        api_key = os.environ["SUBLIME_API_KEY"]
        LOGGER.debug(
            "API key found in environment variable: %s", api_key, api_key=api_key
        )
        # Environment variable takes precedence over configuration file content
        config_parser.set("sublime", "api_key", api_key)

    return {
        "api_key": config_parser.get("sublime", "api_key")
    }


def save_config(config):
    """Save configuration.

    :param config: Data to be written to the configuration file.
    :type config:  dict

    """
    config_parser = ConfigParser()
    config_parser.add_section("sublime")
    config_parser.set("sublime", "api_key", config["api_key"])

    config_parser_existing = ConfigParser()
    if os.path.isfile(CONFIG_FILE):
        LOGGER.debug("Reading configuration file: %s...", CONFIG_FILE, path=CONFIG_FILE)
        with open(CONFIG_FILE) as config_file:
            config_parser_existing.readfp(config_file)

        # if an emailrep key exists, ensure we don't overwrite it
        try:
            emailrep_key = config_parser_existing.get("emailrep", "key")
            if emailrep_key:
                config_parser.add_section("emailrep")
                config_parser.set("emailrep", "key", emailrep_key)
        except:
            pass

    config_dir = os.path.dirname(CONFIG_FILE)
    if not os.path.isdir(config_dir):
        os.makedirs(config_dir)

    with open(CONFIG_FILE, "w") as config_file:
        config_parser.write(config_file)

