"""Helper functions to reduce subcommand duplication."""

import sys
import email
import base64
import json
from pathlib import Path

import click
import structlog
import yaml
import msg_parser

from sublime.error import *

LOGGER = structlog.get_logger()


def load_eml(input_file):
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

def load_msg(input_file):
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

def load_message_data_model(input_file):
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
    rules, queries = [], []
    for rules_file in Path(files_path).rglob("*.yml"):
        with rules_file.open(encoding='utf-8') as f:
            try:
                rules_tmp, queries_tmp = load_yml_file(f)
                if rules_tmp:
                    rules.extend(rules_tmp)
                if queries_tmp:
                    queries.extend(queries_tmp)
            except LoadRuleError as error:
                # We want to ignore errors and continue reading the rest 
                # of the files. 
                if ignore_errors:
                    LOGGER.warning(error.message)
                else:
                    raise

    if len(rules) == 0 and len(queries) == 0:
        LOGGER.warning("No valid YML files found in {}".format(files_path))

    return rules, queries


def load_yml_file(yml_file, ignore_errors=True):
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
            error_str = f"Missing source in {yml_file.name}'"
            if ignore_errors:
                LOGGER.warning(error_str)
                return None
            raise LoadRuleError(error_str)
        return {
                "source": yaml_dict.get("source"),
                "name": yaml_dict.get("name"),
        }

    for rule_yaml in rules_yaml:
        rule = safe_yaml_filter(rule_yaml)

        if rule:
            rules.append(rule)

    for query_yaml in queries_yaml:
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
