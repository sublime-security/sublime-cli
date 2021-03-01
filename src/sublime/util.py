"""Utility and helper functions."""

import os
import socket
import sys
import email
import mailbox
import base64
import json

import yaml
import click
import structlog
import msg_parser
from halo import Halo
from six.moves.configparser import ConfigParser
from pathlib import Path

from sublime.error import *

CONFIG_FILE = os.path.expanduser(os.path.join("~", ".config", "sublime", "setup.cfg"))
LOGGER = structlog.get_logger()

DEFAULT_CONFIG = {"api_key": "", "save_dir": "", "permission": ""}

CONFIRMATION_MESSAGE = """
    Messages will be sent to Sublime Security servers for analysis.
    
    This message is intended to preserve your privacy. You only need to accept once.
    
    Would you like to continue?

"""

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
        # LOGGER.debug("Parsing configuration file: %s..." % CONFIG_FILE)
        with open(CONFIG_FILE) as config_file:
            config_parser.readfp(config_file)
    else:
        # LOGGER.debug("Configuration file not found: %s" % CONFIG_FILE)
        pass

    if "SUBLIME_API_KEY" in os.environ:
        api_key = os.environ["SUBLIME_API_KEY"]
        # LOGGER.debug("API key found in environment variable: %s", api_key, api_key=api_key)
        # Environment variable takes precedence over configuration file content
        config_parser.set("sublime", "api_key", api_key)

    if "SUBLIME_SAVE_DIR" in os.environ:
        save_dir = os.environ["SUBLIME_SAVE_DIR"]
        # LOGGER.debug("Save dir found in environment variable: %s", save_dir, save_dir=save_dir)
        # Environment variable takes precedence over configuration file content
        config_parser.set("sublime", "save_dir", save_dir)

    return {
        "api_key": config_parser.get("sublime", "api_key"),
        "save_dir": config_parser.get("sublime", "save_dir"),
        "permission": config_parser.get("sublime", "permission"),
    }


def save_config(config):
    """Save configuration.

    :param config: Data to be written to the configuration file.
    :type config:  dict

    """
    config_parser = ConfigParser()
    config_parser.add_section("sublime")

    if len(config) == 0:
        click.echo('Error: no options provided. Try "sublime setup -h" for help.')
        click.get_current_context().exit(-1)

    # If either value was not specified, load the existing values saved
    # to ensure we don't overwrite their values to null here
    saved_config = load_config()
    if 'api_key' not in config or not config['api_key']:
        config['api_key'] = saved_config['api_key']
    if 'save_dir' not in config or not config['save_dir']:
        config['save_dir'] = saved_config['save_dir']
    if 'permission' not in config or not config['permission']:
        config['permission'] = saved_config['permission']

    if config["save_dir"] and not os.path.isdir(config["save_dir"]):
        click.echo("Error: save directory is not a valid directory")
        click.get_current_context().exit(-1)

    config_parser.set("sublime", "api_key", config["api_key"])
    config_parser.set("sublime", "save_dir", config["save_dir"])
    config_parser.set("sublime", "permission", config["permission"])

    config_parser_existing = ConfigParser()
    if os.path.isfile(CONFIG_FILE):
        # LOGGER.debug("Reading configuration file: %s...", CONFIG_FILE, path=CONFIG_FILE)
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


def request_permission():
    config = load_config()
    permission = config['permission'] 
    if not permission or permission != "True":
        if click.confirm(CONFIRMATION_MESSAGE, abort=True):
            config['permission'] = "True"
            save_config(config)


def load_eml(input_file):
    """Load .EML file.

    :param input_file: Path to file.
    :type input_file: str
    :returns: Base64-encoded raw content
    :rtype: string
    :raises: LoadEMLError

    """
    with open(input_file) as f:
        return load_eml_file_handle(f)


def load_eml_file_handle(input_file):
    """Load .EML file.

    :param input_file: File handle.
    :type input_file: _io.TextIOWrapper
    :returns: Base64-encoded raw content
    :rtype: string
    :raises: LoadEMLError

    """
    if input_file is None:
        raise LoadEMLError("Missing .eml file")

    try:
        message = email.message_from_file(input_file)
        raw_message_base64 = base64.b64encode(
                message.as_string().encode('utf-8')).decode('ascii')

        # fails for utf-8 messages:
        # decoded = base64.b64encode(message.as_bytes()).decode('ascii') 
    except Exception as exception:
        error_message = "{}".format(exception)
        raise LoadEMLError(error_message)

    return raw_message_base64


def load_msg(filepath):
    """Load .MSG file.

    :param filepath: Path to file.
    :type filepath: str
    :returns: Base64-encoded raw content
    :rtype: string
    :raises: LoadMSGError

    """

    with open(filepath) as f:
        return load_msg_file_handle(f)


def load_msg_file_handle(input_file):
    """Load .MSG file.

    :param input_file: File handle.
    :type input_file: _io.TextIOWrapper
    :returns: Base64-encoded raw content
    :rtype: string
    :raises: LoadMSGError

    """
    if input_file is None:
        raise LoadMSGError("Missing .msg file")

    try:
        msg_obj = msg_parser.MsOxMessage(input_file.name)
        email_formatter = msg_parser.email_builder.EmailFormatter(msg_obj)
        message_str = email_formatter.build_email()

        raw_message_base64 = base64.b64encode(
                message_str.encode('utf-8')).decode('ascii')
    except Exception as exception:
        error_message = "{}".format(exception)
        raise LoadMSGError(error_message)

    return raw_message_base64

def load_mbox(filepath, halo=None):
    """Load .MBOX file.

    :param filepath: Path to file.
    :type filepath: str
    :returns: Base64-encoded raw content
    :rtype: map of (key: subject+index, value: raw_message)
    :raises: LoadMBOXError

    """
    if halo:
        _, _, file_name = filepath.rpartition('/')
        halo.text = f"Loading ({file_name}) this may take a while..."

    raw_messages = {}
    mbox = mailbox.mbox(filepath)
    num_messages = len(mbox)

    for i in range(num_messages):
        message = mbox[i]
        if halo:
            halo.text = f"Encoding ({file_name}) message {i+1} of {num_messages}"

        try:
            # identify a suitable key for this message
            instance = 0
            subject = message['subject'] or "[Empty Subject]"
            key = subject
            while key in raw_messages:
                instance += 1
                key = subject + f" ({instance})"

            # encode the raw message and return
            raw_message = message.as_string().encode('utf-8')
            raw_messages[key] = base64.b64encode(raw_message).decode('ascii')

        except Exception as exception:
            if halo: halo.stop()
            LOGGER.warning(f"failed to decode {key}: {exception}")
            if halo: halo.start()
            # raise LoadMBOXError(error_message)

    return raw_messages

def load_message_data_model(filepath):
    """Load Message Data Model file.

    :param filepath: Path to file.
    :type filepath: str
    :returns: Message Data Model JSON object
    :rtype: dict
    :raises: LoadMessageDataModelError

    """
    with open(filepath) as f:
        return load_message_data_model_file_handle(f)


def load_message_data_model_file_handle(input_file):
    """Load Message Data Model file.

    :param input_file: File handle.
    :type input_file: _io.TextIOWrapper
    :returns: Message Data Model JSON object
    :rtype: dict
    :raises: LoadMessageDataModelError

    """
    if input_file is None:
        raise LoadMessageDataModelError("Missing Message Data Model file")
    
    try:
        message_data_model = json.load(input_file)
    except Exception as exception:
        error_message = "{}".format(exception)
        raise LoadMessageDataModelError(error_message)

    return message_data_model


def load_yml_path(files_path, ignore_errors=True):
    """Load rules and queries from a path.

    :param files_path: Path to YML files
    :type files_path: string
    :param ignore_errors: Ignore file loading errors
    :type ignore_errors: boolean
    :returns: A list of rules and a list of queries
    :rtype: list, list
    :raises: LoadRuleError

    """
    # gather all rules files
    sqar_files = []
    for file in Path(files_path).rglob("*.yml"):
        sqar_files.append(file)
    for file in Path(files_path).rglob("*.yaml"):
        sqar_files.append(file)

    # get all rules and queries from
    rules, queries = [], []
    for file in sqar_files:
        with file.open(encoding='utf-8') as f:
            try:
                rules_tmp, queries_tmp = load_yml(f)
                if rules_tmp:
                    rules.extend(rules_tmp)
                if queries_tmp:
                    queries.extend(queries_tmp)
            except LoadRuleError as error:
                # Ignore errors and continue reading the remaining files.
                if ignore_errors:
                    LOGGER.warning(error.message)
                else:
                    raise

    if len(rules) == 0 and len(queries) == 0:
        LOGGER.warning(f"No valid YAML files found in {files_path}")

    return rules, queries


def load_yml(yml_file, ignore_errors=True):
    """Load rules and queries from a file.

    :param yml_file: YML file
    :type yml_file: _io.TextIOWrapper
    :param ignore_errors: Ignore loading errors
    :type ignore_errors: boolean
    :returns: A list of rules and a list of queries
    :rtype: list, list
    :raises: LoadRuleError

    """
    if yml_file is None:
        if ignore_errors:
            LOGGER.warning("Missing YML file")
            return [], []
        else:
            raise LoadRuleError("Missing YML file")

    try:
        rules_and_queries_yaml = yaml.load(yml_file, Loader=yaml.SafeLoader)
        if not rules_and_queries_yaml or not isinstance(rules_and_queries_yaml, dict):
            if ignore_errors:
                LOGGER.warning("Invalid YML file")
                return [], []
            else:
                raise LoadRuleError("Invalid YML file")
    except yaml.scanner.ScannerError as e:
        error = """File '{}' contains invalid characters: {}""".format(yml_file.name, e)
        raise LoadRuleError(error)
    except Exception as e:
        raise LoadRuleError(e)

    rules_yaml, queries_yaml = rules_and_queries_yaml.get("rules", []), rules_and_queries_yaml.get("queries", [])
    rules, queries = [], []

    if not rules_yaml and not queries_yaml:
        rule_or_query_yaml = rules_and_queries_yaml

        # default to query
        if "type" not in rule_or_query_yaml:
            rule_or_query_yaml["type"] = "query"

        if rule_or_query_yaml.get("type") not in ["rule", "query"]:
            error_str = f'Invalid type in {yml_file.name}'
            if ignore_errors:
                LOGGER.warning(error_str)
                return [], []
            raise LoadRuleError(error_str)

        if rule_or_query_yaml.get("type") == "rule":
            rules_yaml.append(rule_or_query_yaml)
        else:
            queries_yaml.append(rule_or_query_yaml)

    def safe_yaml_filter(yaml_dict):
        if not yaml_dict.get("source"):
            error_str = f"Missing source in '{yml_file.name}'"
            raise LoadRuleError(error_str)
        return {
                "source": yaml_dict.get("source"),
                "name": yaml_dict.get("name"),
        }

    for rule_yaml in rules_yaml:
        if not isinstance(rule_yaml, dict):
            error_str = f"Invalid list of rules"
            raise LoadRuleError(error_str)

        rule = safe_yaml_filter(rule_yaml)

        if rule:
            rules.append(rule)

    for query_yaml in queries_yaml:
        if not isinstance(query_yaml, dict):
            error_str = f"Invalid list of queries"
            raise LoadRuleError(error_str)

        query = safe_yaml_filter(query_yaml)

        if query:
            queries.append(query)

    return rules, queries


def get_datetime_formats():
    formats=[
            '%Y-%m-%d',
            '%Y-%m-%dT%H:%M:%S',
            '%Y-%m-%dT%H:%M:%S.%f%z',
            '%Y-%m-%d %H:%M:%S'
    ]

    return formats
