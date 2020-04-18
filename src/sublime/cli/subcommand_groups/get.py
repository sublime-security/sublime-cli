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
@click.option("-a", "--active", "active",
    type=click.Choice(['true', 'false'], case_sensitive=False),
    help="Filter by active or inactive detections"
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
    if active == 'true':
        active = True
    elif active == 'false':
        active = False
    else:
        active = None

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
    help="Invert: Return not-flagged messages from the last 30 minutes")
@click.option(
    "--reviewed", "reviewed",
    type=click.Choice(['true', 'false'], case_sensitive=False),
    help=(
        "Filter by review status. The default is False unless --safe is "
        "specified, in which case the default is True"
    )
)
@click.option(
    "--safe", "safe",
    type=click.Choice(['true', 'false'], case_sensitive=False),
    help=(
        "Filter by whether the message threat status has been set "
        "to safe or not safe"
    )
)
@click.option("--after", "after", 
    type=click.DateTime(formats=get_datetime_formats()),
    help=(
        "Only retrieve messages after this date. "
        "Default: 30 days ago. Format: ISO 8601"
    )
)
@click.option("--before", "before",
    type=click.DateTime(formats=get_datetime_formats()),
    help="Only retrieve messages before this date. Format: ISO 8601")
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
    reviewed,
    safe,
    after,
    before,
    message_data_model_id,
    output_file,
    output_format,
    verbose,
):
    """
    Get messages. By default, only flagged messages are returned.
    """

    if not message_data_model_id:
        if safe is None and reviewed is None:
            # If neither safe nor reviewed were specified,
            # the default reviewed value is False.
            reviewed = False
        elif safe is not None and reviewed is None:
            # If safe was specified and reviewed was not,
            # the default reviewed value is True.
            reviewed = True
        else:
            # In all other instances, 
            # we use the user's values and don't set anything explicitly
            pass

        results = api_client.get_flagged_messages(
                result, 
                after, 
                before,
                reviewed,
                safe)
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
def org(
    context,
    api_client,
    api_key,
    output_file,
    output_format,
    verbose,
):
    """Get information about the currently authenticated organization."""

    result = api_client.get_org(verbose)

    return result
    
@get.command()
@click.option("-v", "--verbose", count=True, help="Verbose output")
@click.option("-k", "--api-key", help="Key to include in API requests")
@click.option("-a", "--active", "license_active",
    type=click.Choice(['true', 'false'], case_sensitive=False),
    help="Filter by users with active licenses only")
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
def users(
    context,
    api_client,
    api_key,
    license_active,
    output_file,
    output_format,
    verbose,
):
    """Get users."""
    if license_active == 'true':
        license_active = True
    elif license_active == 'false':
        license_active = False
    else:
        license_active = None

    results = api_client.get_users(license_active, verbose)

    return results
