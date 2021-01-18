"""Utility functions."""

import os
import socket

import structlog
import click
from six.moves.configparser import ConfigParser

CONFIG_FILE = os.path.expanduser(os.path.join("~", ".config", "sublime", "setup.cfg"))
LOGGER = structlog.get_logger()

DEFAULT_CONFIG = {"api_key": "", "save_dir": ""}


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
        LOGGER.debug("Parsing configuration file: %s..." % CONFIG_FILE)
        with open(CONFIG_FILE) as config_file:
            config_parser.readfp(config_file)
    else:
        LOGGER.warning("Configuration file not found: %s" % CONFIG_FILE)

    if "SUBLIME_API_KEY" in os.environ:
        api_key = os.environ["SUBLIME_API_KEY"]
        LOGGER.debug(
            "API key found in environment variable: %s", api_key, api_key=api_key
        )
        # Environment variable takes precedence over configuration file content
        config_parser.set("sublime", "api_key", api_key)

    if "SUBLIME_SAVE_DIR" in os.environ:
        save_dir = os.environ["SUBLIME_SAVE_DIR"]
        LOGGER.debug(
            "Save dir found in environment variable: %s", save_dir, save_dir=save_dir
        )
        # Environment variable takes precedence over configuration file content
        config_parser.set("sublime", "save_dir", save_dir)

    return {
        "api_key": config_parser.get("sublime", "api_key"),
        "save_dir": config_parser.get("sublime", "save_dir")
    }


def save_config(config):
    """Save configuration.

    :param config: Data to be written to the configuration file.
    :type config:  dict

    """
    config_parser = ConfigParser()
    config_parser.add_section("sublime")

    if not config["api_key"] and not config["save_dir"]:
        click.echo('Error: no options provided. Try "sublime setup -h" for help.')
        click.get_current_context().exit(-1)

    # If either value was not specified, load the existing values saved
    # to ensure we don't overwrite their values to null here
    if not config["api_key"] or not config["save_dir"]:
        saved_config = load_config()
        if not config["api_key"]:
            config["api_key"] = saved_config["api_key"]
        if not config["save_dir"]:
            config["save_dir"] = saved_config["save_dir"]

    if config["save_dir"] and not os.path.isdir(config["save_dir"]):
        click.echo("Error: save directory is not a valid directory")
        click.get_current_context().exit(-1)

    config_parser.set("sublime", "api_key", config["api_key"])
    config_parser.set("sublime", "save_dir", config["save_dir"])

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
