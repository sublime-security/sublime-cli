"""CLI subscribe subcommands."""

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
def subscribe():
    """Subscribe or unsubscribe from items in the Sublime community."""
    pass

@subscribe.command()
@click.option("-v", "--verbose", count=True, help="Verbose output")
@click.option("-k", "--api-key", help="Key to include in API requests")
@click.option("-i", "--id", "detection_id", 
        help="Detection ID")
@click.option("-n", "--name", "detection_name", 
        help="Detection name")
@click.option("--org-id", "created_by_org_id", 
        help="All detections authored by a specific org ID")
@click.option("--sublime-user-id", "created_by_sublime_user_id", 
        help="All detections authored by a specific sublime user ID")
@click.option("-a", "--active", "active", default="false", show_default=True,
    type=click.Choice(['true', 'false'], case_sensitive=False),
    help="State of the detection after subscribing"
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
    created_by_org_id,
    created_by_sublime_user_id,
    active,
    output_file,
    output_format,
    verbose,
):
    """Subscribe to detections."""

    results = {"success": [], "fail": []}
    if detection_id:
        results["success"] = [api_client.subscribe_community_detection(
                detection_id=detection_id,
                active=active)]
    elif detection_name:
        results["success"] = [api_client.subscribe_community_detection_by_name(
                detection_name=detection_name,
                active=active)]
    elif created_by_org_id or created_by_sublime_user_id:
        detections = api_client.get_community_detections(
                created_by_org_id=created_by_org_id,
                created_by_sublime_user_id=created_by_sublime_user_id)

        if not detections:
            LOGGER.error("No detections matched the given criteria")
            context.exit(-1)

        count = len(detections)
        message = f"Are you sure you want to subscribe to all {count} detections?" 
        if click.confirm(message, abort=False):
            for detection in detections["detections"]:
                try:
                    results["success"].append(
                            api_client.subscribe_community_detection(
                                detection_id=detection["id"],
                                active=active))
                except Exception as e:
                    results["fail"].append(e)
        else:
            click.echo("Aborted!")
            context.exit(-1)
    else:
        LOGGER.error("Missing item(s) to subscribe to")
        context.exit(-1)

    return results
