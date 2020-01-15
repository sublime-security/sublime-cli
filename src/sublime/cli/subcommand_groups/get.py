"""CLI get subcommands."""

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
def get():
    """Get items from your Sublime environment."""
    pass

@get.command()
@click.option("-v", "--verbose", count=True, help="Verbose output")
@click.option("-k", "--api-key", help="Key to include in API requests")
@click.option("-i", "--id", "detection_id", 
        help="Detection ID")
@click.option("-n", "--name", "detection_name", 
        help="Detection name")
@click.option("-a", "--active", "active", is_flag=True, default=False,
        help="Filter by active detections only")
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
def detections(
    context,
    api_client,
    api_key,
    detection_id,
    detection_name,
    active,
    output_file,
    output_format,
    verbose,
):
    """Get detections."""

    results = {}
    if detection_id:
        results["detections"] = [api_client.get_detection_by_id(
            detection_id, verbose)]
    elif detection_name:
        results["detections"] = [api_client.get_detection_by_name(
            detection_name, verbose)]
    else:
        results = api_client.get_detections(active)

    if results.get("detections"):
        results["detections"] = sorted(results["detections"], 
                key=lambda i: i["name"] if i.get("name") else "")

    return results

@get.command()
@click.option("-v", "--verbose", count=True, help="Verbose output")
@click.option("-k", "--api-key", help="Key to include in API requests")
@click.option("-n", "--not", "result", is_flag=True, default=True,
        help="Invert: Return not-flagged messages")
@click.option("-i", "--id", "message_data_model_id", 
        help="Message Data Model ID")
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
def messages(
    context,
    api_client,
    api_key,
    result,
    message_data_model_id,
    output_file,
    output_format,
    verbose,
):
    """Get messages. By default, flagged messages are returned."""

    if not message_data_model_id:
        results = api_client.get_flagged_messages(result)
    else:
        results = api_client.get_flagged_message_detail(message_data_model_id)

    return results

@get.command()
@click.option("-v", "--verbose", count=True, help="Verbose output")
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
def me(
    context,
    api_client,
    api_key,
    output_file,
    output_format,
    verbose,
):
    """Get information about the currently authenticated Sublime user."""

    result = api_client.get_me(verbose)

    return result
    
