"""CLI send subcommands."""

import os
import platform

import click
import structlog

from sublime.__version__ import __version__
from sublime.cli.decorator import (
    echo_result,
    handle_exceptions,
    pass_api_client,
    MissingDetectionInput
)
from sublime.cli.helper import *

LOGGER = structlog.get_logger()

@click.group()
def send():
    """Send or generate mock data."""
    pass

@send.command()
@click.option("-v", "--verbose", count=True, help="Verbose output")
@click.option("-k", "--api-key", help="Key to include in API requests")
@click.argument("command")
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
def mock(
    context,
    api_client,
    api_key,
    command,
    output_file,
    output_format,
    verbose,
):
    """Send mock email messages to yourself.

    Commands: "tutorial-one"

    """

    if command == "tutorial-one":
        result = api_client.send_mock_tutorial_one()
    else:
        LOGGER.error("Invalid command")
        context.exit(-1)

    return result
