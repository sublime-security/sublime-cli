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
    help="Invert: Return not-flagged messages")
@click.option(
    "--reviewed", "reviewed",
    type=click.Choice(['true', 'false'], case_sensitive=False),
    default="false", show_default=True,
    help="Filter by review status"
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
        results = api_client.get_flagged_messages(
                result, 
                after, 
                before,
                reviewed)
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
    type=click.Choice(['true', 'false'], case_sensitive=False), default="true",
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

    results["users"] = sorted(results["users"], 
            key=lambda i: i["email_address"])

    return results
