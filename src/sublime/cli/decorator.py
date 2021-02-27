"""CLI subcommand decorators.

Decorators used to add common functionality to subcommands.

"""
import os
import functools
import base64

import click
import structlog
from requests.exceptions import RequestException

from sublime.api import Sublime
from sublime.cli.formatter import FORMATTERS, ANSI_MARKUP
from sublime.error import *
from sublime.util import load_config

LOGGER = structlog.get_logger()


def echo_result(function):
    """Decorator that prints subcommand results correctly formatted.

    :param function: Subcommand that returns a result from the API.
    :type function: callable
    :returns: Wrapped function that prints subcommand results
    :rtype: callable

    """

    @functools.wraps(function)
    def wrapper(*args, **kwargs):
        result = function(*args, **kwargs)
        context = click.get_current_context()
        params = context.params
        if params.get("output_format"):
            output_format = params["output_format"]
        else:
            output_format = "txt"
        formatter = FORMATTERS[output_format]
        config = load_config()
        if isinstance(formatter, dict):
            # For the text formatter, there's a separate formatter for each 
            if isinstance(context.parent.command, click.Group) and \
                    context.parent.command.name != 'main':
                # sub-sub command
                parent_name = context.parent.command.name
                cur_name = context.command.name
                name = f"{parent_name}_{cur_name}"
                formatter = formatter[name]
            else:
                # regular subcommand
                formatter = formatter[context.command.name]

        if context.command.name == "create":
            # default behavior is to always save the MDM
            # even if no output file is specified
            if not params.get("output_file"):
                input_file_relative_name = params.get('input_file').name
                input_file_relative_no_ext, _ = os.path.splitext(
                        input_file_relative_name)
                input_file_name_no_ext = os.path.basename(
                        input_file_relative_no_ext)
                output_file_name = f'{input_file_name_no_ext}'

                if output_format == "json":
                    output_file_name += ".mdm"
                elif output_format == "txt":
                    output_file_name += ".txt"

                # if the user has a default save directory configured,
                # store the MDM there
                if config["save_dir"]:
                    output_file_name = os.path.join(config["save_dir"], output_file_name)

                params["output_file"] = click.open_file(output_file_name, 
                        mode="w")

            # strip the extra info and just save the unenriched MDM
            result = result["data_model"]

        output = formatter(result, 
                params.get("verbose", False)).strip("\n")

        click.echo(
            output, 
            file=params.get("output_file", click.open_file("-", mode="w"))
        )

        file_name = params.get("output_file")
        if file_name:
            click.echo(ANSI_MARKUP(f"Output saved to <bold>{file_name.name}</bold>"))

    return wrapper


def handle_exceptions(function):
    """Print error and exit on API client errors.

    :param function: Subcommand that returns a result from the API.
    :type function: callable
    :returns: Wrapped function that prints subcommand results
    :rtype: callable

    """

    @functools.wraps(function)
    def wrapper(*args, **kwargs):
        try:
            return function(*args, **kwargs)
        except RateLimitError as error:
            error_message = "API error: {}".format(error.message)
            LOGGER.error(error_message)
            click.get_current_context().exit(-1)
        except InvalidRequestError as error:
            error_message = "API error: {}".format(error.message)
            LOGGER.error(error_message)
            click.get_current_context().exit(-1)
        except APIError as error:
            error_message = "API error: {}".format(error.message)
            LOGGER.error(error_message)
            click.get_current_context().exit(-1)
        except LoadRuleError as error:
            error_message = "Load rule error: {}".format(error.message)
            LOGGER.error(error_message)
            click.get_current_context().exit(-1)
        except LoadEMLError as error:
            error_message = "Load EML error: {}".format(error.message)
            LOGGER.error(error_message)
            click.get_current_context().exit(-1)
        except LoadMSGError as error:
            error_message = "Load MSG error: {}".format(error.message)
            LOGGER.error(error_message)
            click.get_current_context().exit(-1)
        except LoadMessageDataModelError as error:
            error_message = "Load MDM error: {}".format(error.message)
            LOGGER.error(error_message)
            click.get_current_context().exit(-1)
        except RequestException as error:
            error_message = "Request error: {}".format(error)
            LOGGER.error(error_message)
            click.get_current_context().exit(-1)
        except AuthenticationError as error:
            error_message = "API error: {}".format(error)
            LOGGER.error(error_message)

            # check to see if an API key is present, if not 
            # print a helpful message
            context = click.get_current_context()
            api_key = context.params.get("api_key")
            config = load_config()

            if api_key is None:
                if not config["api_key"]:
                    prog_name = context.parent.info_name
                    click.echo(
                        "\nError: API key not found.\n\n"
                        "To fix this problem, please use any of the following methods "
                        "(in order of precedence):\n"
                        "- Pass it using the -k/--api-key option.\n"
                        "- Set it in the SUBLIME_API_KEY environment variable.\n"
                        "- Run 'setup -k' to save it to the configuration file.\n"
                    )
            click.get_current_context().exit(-1)

    return wrapper


def pass_api_client(function):
    """Create API client form API key and pass it to subcommand.

    :param function: Subcommand that returns a result from the API.
    :type function: callable
    :returns: Wrapped function that prints subcommand results
    :rtype: callable

    """

    @functools.wraps(function)
    def wrapper(*args, **kwargs):
        context = click.get_current_context()
        api_key = context.params.get("api_key")
        config = load_config()

        if api_key is None:
            if not config["api_key"]:
                pass
                '''
                prog_name = context.parent.info_name
                click.echo(
                    "\nError: API key not found.\n\n"
                    "To fix this problem, please use any of the following methods "
                    "(in order of precedence):\n"
                    "- Pass it using the -k/--api-key option.\n"
                    "- Set it in the SUBLIME_API_KEY environment variable.\n"
                    "- Run 'setup -k' to save it to the configuration file.\n"
                )
                context.exit(-1)
                '''
            else:
                api_key = config["api_key"]

        api_client = Sublime(api_key=api_key)
        return function(api_client, *args, **kwargs)

    return wrapper


def create_command(function):
    """Decorator that groups decorators common to create subcommand."""

    @click.command()
    @click.option("-k", "--api-key", help="Key to include in API requests [optional]")
    @click.option(
        "-i", "--input", "input_file", type=click.File(), 
        help="Input EML file", required=True
    )
    @click.option("-t", "--type", "message_type",
        type=click.Choice(['inbound', 'internal', 'outbound'], case_sensitive=False),
        default="inbound",
        show_default=True,
        help="Set the message type [optional]"
    )
    @click.option(
        "-o", "--output", "output_file", type=click.File(mode="w"), 
        help=(
            "Output file. Defaults to the input_file name in the current "
            "directory with a .mdm extension if none is specified"
        )
    )
    @click.option(
        "-f",
        "--format",
        "output_format",
        type=click.Choice(["json", "txt"]),
        default="json",
        show_default=True,
        help="Output format",
    )
    @click.option("-m", "--mailbox", "mailbox_email_address",
            help="Mailbox email address that received the message [optional]"
    )
    @pass_api_client
    @click.pass_context
    @echo_result
    @handle_exceptions
    @functools.wraps(function)
    def wrapper(*args, **kwargs):
        return function(*args, **kwargs)

    return wrapper


def analyze_command(function):
    """Decorator that groups decorators common to analyze subcommand."""

    @click.command()

    @click.option("-k", "--api-key", "api_key",
            help="Key to include in API requests [optional]")

    @click.option("-i", "--input", "input_path",
        type=click.Path(exists=True),
        help="Input file or directory (.eml, .msg, .mdm and .mbox supported)",
        required=True)

    @click.option("-r", "--run", "run_path",
        type=click.Path(exists=True), 
        help=(
            "Rule/query file or directory (.yml and .yaml supported). "
            "Queries outputs that return false, null, [], {} are not displayed by default"
            )
        )

    @click.option("-q", "--query", "query",
        type=str,
        help=("Raw MQL. Instead of using a rules file, "
            "provide raw MQL, surrounded by single quotes"))

    @click.option("-t", "--type", "message_type",
        type=click.Choice(['inbound', 'internal', 'outbound'], case_sensitive=False),
        default="inbound",
        show_default=True,
        help="Set the message type (EML and MSG files only) [optional]")

    @click.option("-m", "--mailbox", "mailbox_email_address",
        help=("Mailbox email address that received the "
            "message (EML and MSG files only) [optional]"))

    @click.option("-o", "--output", "output_file",
        type=click.File(mode="w"), 
        help="Output file")

    @click.option("-f", "--format", "output_format",
        type=click.Choice(["json", "txt"]),
        default="txt",
        help="Output format")

    @pass_api_client
    @click.pass_context
    @echo_result
    @handle_exceptions
    @functools.wraps(function)
    def wrapper(*args, **kwargs):
        return function(*args, **kwargs)

    return wrapper


def me_command(function):
    """Decorator that groups decorators common to me subcommand."""

    @click.command()
    @click.option("-k", "--api-key", help="Key to include in API requests")
    @click.option(
        "-o", "--output", "output_file", type=click.File(mode="w"), 
        help="Output file"
    )
    @click.option(
        "-f",
        "--format",
        "output_format",
        type=click.Choice(["json", "txt"]),
        default="txt",
        help="Output format",
    )
    @pass_api_client
    @click.pass_context
    @echo_result
    @handle_exceptions
    @functools.wraps(function)
    def wrapper(*args, **kwargs):
        return function(*args, **kwargs)

    return wrapper


def feedback_command(function):
    """Decorator that groups decorators common to me subcommand."""

    @click.command()
    @click.argument("feedback", type=str)
    @pass_api_client
    @click.pass_context
    @echo_result
    @handle_exceptions
    @functools.wraps(function)
    def wrapper(*args, **kwargs):
        return function(*args, **kwargs)

    return wrapper


class MissingRuleInput(click.ClickException):
    """Exception used for analyze commands missing a YAML file or MQL
    """

    def __init__(self):
        message = (
                "You must specify either a YAML file/directory (-r) "
                "or raw MQL (-q)"
                )
        super(MissingRuleInput, self).__init__(message)


class SubcommandNotImplemented(click.ClickException):
    """Exception used temporarily for subcommands that have not been implemented.

    :param subcommand_name: Name of the subcommand to display in the error message.
    :type subcommand_function: str

    """

    def __init__(self, subcommand_name):
        message = "{!r} subcommand is not implemented yet.".format(subcommand_name)
        super(SubcommandNotImplemented, self).__init__(message)


def not_implemented_command(function):
    """Decorator that sends requests for not implemented commands."""

    @click.command()
    @pass_api_client
    @functools.wraps(function)
    def wrapper(api_client, *args, **kwargs):
        command_name = function.__name__
        try:
            api_client._not_implemented(command_name)
        except Exception:
            raise SubcommandNotImplemented(command_name)

    return wrapper
