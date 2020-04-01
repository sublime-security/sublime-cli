"""CLI delete subcommands."""

import os
import platform

import click

from sublime.__version__ import __version__
from sublime.cli.decorator import (
    echo_result,
    handle_exceptions,
    pass_api_client,
    MissingDetectionInput
)
from sublime.cli.helper import *


@click.group()
def delete():
    """Delete an item(s) in your Sublime environment."""
    pass

@delete.command()
@click.option("-v", "--verbose", count=True, help="Verbose output")
@click.option("-k", "--api-key", help="Key to include in API requests")
@click.option(
    "-i", "--message-data-model-id", "message_data_model_id", 
    help="Message Data Model ID", required=True
)
@click.option(
    "-p", "--permanent", "permanent", is_flag=True,
    help="Permanently delete the message (don't send to Trash)"
)
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
@click.option("-v", "--verbose", count=True, help="Verbose output")
def messages(
    context,
    api_client,
    api_key,
    message_data_model_id,
    permanent,
    output_file,
    output_format,
    verbose,
):
    """Delete a message from a user's mailbox using the Message Data Model ID"""

    result = api_client.delete_model_external_message(message_data_model_id, permanent)
    results = [result]

    return results
