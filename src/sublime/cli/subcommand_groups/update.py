"""CLI update subcommands."""

import os
import platform

import click
import structlog
from halo import Halo

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
def update():
    """Update an item(s) in your Sublime environment."""
    pass

@update.command()
@click.option("-v", "--verbose", count=True, help="Verbose output")
@click.option("-k", "--api-key", help="Key to include in API requests")
@click.option(
    "-D", "--detections", "detections_path", 
    type=click.Path(exists=True), 
    help="Detections file or directory"
)
@click.option("-i", "--id", "detection_id",
        help="Update using detection ID")
@click.option(
    "-d", "--detection", "detection_str", type=str,
    help=(
        "Raw detection. Instead of using a detections file, "
        "specify a single detection to be run directly surrounded "
        "by single quotes"
    )
)
@click.option(
    "-n", "--name", "detection_name", type=str,
    help=(
        "Update using detection name. "
        "If a detection ID is provided, this will change the detection name"
    )
)
@click.option("-a", "--active", "active", 
    type=click.Choice(['true', 'false'], case_sensitive=False),
    help="Enable or disable the detection for live flow"
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
    detections_path,
    detection_id,
    detection_str,
    detection_name,
    active,
    output_file,
    output_format,
    verbose,
):
    """Update a detection(s)."""
    if active == 'true':
        active = True
    elif active == 'false':
        active = False
    else:
        active = None

    results = {"success": [], "fail": []}
    if detections_path:
        if os.path.isfile(detections_path):
            with open(detections_path, encoding='utf-8') as f:
                detections = load_detections(f)

        elif os.path.isdir(detections_path):
            detections = load_detections_path(detections_path)

        if detection_name or detection_id:
            message = (
                    "Specify one of either a PQL file, detection ID, or detection name."
            )
            LOGGER.error(message)
            context.exit(-1)

        for d in detections:

            try:
                results["success"].append(
                        api_client.update_detection_by_name(
                    d.get("name"), d.get("detection"), active))
            except Exception as e:
                results["fail"].append(e)

    else:
        if not detection_id and not detection_name:
            LOGGER.error("Detection ID, detection name, or PQL file(s) is required")
            context.exit(-1)

        # depending on what we're updating, either of these could be null
        detection_str = detection_str if detection_str else ""
        detection_name = detection_name if detection_name else ""

        detections = [create_simple_detection(
            detection_str=detection_str,
            detection_name=detection_name,
            detection_id=detection_id)]

        if detection_id:
            results["success"] = [api_client.update_detection(
                detection_id, d, active) for d in detections]
        else:
            results["success"] = [api_client.update_detection_by_name(
                d.get("name"), d.get("detection"), active) for d in detections]

    results["success"] = sorted(results["success"], 
            key=lambda i: i["original_name"] if i.get("original_name") else "")

    return results

@update.command()
@click.option("-v", "--verbose", count=True, help="Verbose output")
@click.option("-k", "--api-key", help="Key to include in API requests")
@click.option("-i", "--id", "message_data_model_id",
        help="Message data model ID to update"
)
@click.option(
    "--reviewed", "reviewed",
    type=click.Choice(['true', 'false'], case_sensitive=False),
    required=True,
    help="Review status"
)
@click.option("--safe", "safe", 
    type=click.Choice(['true', 'false'], case_sensitive=False),
    required=True,
    help=(
        "Whether the message is safe or not. There are no second "
        "order effects to this (no blacklisting/whitelisting, etc.). "
        "This strictly exists to enable simple filtering later." 
    )
)
@click.option("--all", "review_all", is_flag=True,
    help=(
        "Update the review status/threat status on all messages that "
        "are flagged, not reviewed, and within the timeframe specified"
    )
)
@click.option("--after", "after", 
    type=click.DateTime(formats=get_datetime_formats()),
    help=(
        "For --all, only update messages after this date. "
        "Default: 30 days ago. Format: ISO 8601"
    )
)
@click.option("--before", "before",
    type=click.DateTime(formats=get_datetime_formats()),
    help="For --all, only update messages before this date. Format: ISO 8601"
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
def messages(
    context,
    api_client,
    api_key,
    message_data_model_id,
    reviewed,
    safe,
    review_all,
    after,
    before,
    output_file,
    output_format,
    verbose,
):
    """Update a message(s)."""

    if safe == 'true':
        safe = True
    elif safe == 'false':
        safe = False
    else:
        LOGGER.error("Threat status is required")
        context.exit(-1)

    if review_all:
        results_test = api_client.get_messages(
                result=True,
                after=after,
                before=before,
                reviewed=False)
        count = len(results_test["results"])
        if not count:
            click.echo("No messages to update!")
            context.exit(-1)

        message = f"Are you sure you want to update all {count} messages?" 
        if click.confirm(message, abort=False):
            results = api_client.review_all_messages(
                    after=after,
                    before=before,
                    reviewed=reviewed,
                    safe=safe)

        else:
            click.echo("Aborted!")
            context.exit(-1)
    elif not message_data_model_id:
        LOGGER.error("Message Data Model ID is required")
        context.exit(-1)
    else:
        results = api_client.review_message(
            message_data_model_id=message_data_model_id,
            reviewed=reviewed,
            safe=safe)

    return results

@update.command()
@click.option("-v", "--verbose", count=True, help="Verbose output")
@click.option("-k", "--api-key", help="Key to include in API requests")
@click.option("-u", "--user", "email_address",
        help="Email address of user to update"
)
@click.option("--all", "update_all", is_flag=True,
    help=(
        "Update the status of all users at once"
    )
)
@click.option("-a", "--active", "license_active", 
    type=click.Choice(['true', 'false'], case_sensitive=False), required=True,
    help="Activate/deactivate the user's license for live flow"
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
def users(
    context,
    api_client,
    api_key,
    email_address,
    update_all,
    license_active,
    output_file,
    output_format,
    verbose,
):
    """Update a user(s)."""
    if license_active == 'true':
        license_active = True
    elif license_active == 'false':
        license_active = False
    else:
        LOGGER.error("Invalid user state")
        context.exit(-1)

    if not update_all and not email_address:
        LOGGER.error("You must specify a user or --all")
        context.exit(-1)

    results = {"success": [], "fail": []}
    if update_all:
        all_users = api_client.get_users(license_active=None)
        count = len(all_users["users"])
        if not count:
            click.echo("No users to update!")
            context.exit(-1)

        message = f"Are you sure you want to update all {count} users?" 
        if click.confirm(message, abort=False):
            with Halo(text='This may take a moment', spinner='dots'):
                for user in all_users["users"]:
                    try:
                        if license_active:
                            result = api_client.activate_user(
                                email_address=user["email_address"])
                        else:
                            result = api_client.deactivate_user(
                                email_address=user["email_address"])
                        
                        results["success"].append(result)
                    except Exception as e:
                        results["fail"].append(e)

        else:
            click.echo("Aborted!")
            context.exit(-1)

    else:
        if license_active:
            results["success"] = [api_client.activate_user(
                email_address=email_address)]
        else:
            results["success"] = [api_client.deactivate_user(
                email_address=email_address)]

    return results
