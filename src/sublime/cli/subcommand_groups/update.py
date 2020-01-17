"""CLI update subcommands."""

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
@click.option("--active", "active", 
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
            with open(detections_path) as f:
                detections = load_detections(context, f)

        elif os.path.isdir(detections_path):
            detections = load_detections_path(context, detections_path)

        if detection_name or detection_id:
            message = (
                    "Detection names and IDs cannot be used with a PQL file yet.\n"
                    "Use the -d option to pass the detection in as a string, or "
                    "specify the detection name inside the PQL file."
            )
            click.echo(message)
            context.exit(-1)

        for d in detections:

            try:
                results["success"].append(api_client.update_detection_by_name(
                    d.get("name"), d.get("detection"), active, verbose))
            except Exception as e:
                results["fail"].append(e.args[1])

    else:
        if not detection_id and not detection_name:
            click.echo("Detection ID, detection name, or PQL file(s) is required")
            context.exit(-1)

        # depending on what we're updating, either of these could be null
        detection_str = detection_str if detection_str else ""
        detection_name = detection_name if detection_name else ""

        detections = [create_detection(detection_str, detection_name)]

        if detection_id:
            results["success"] = [api_client.update_detection_by_id(
                detection_id, d, active, verbose) for d in detections]
        else:
            results["success"] = [api_client.update_detection_by_name(
                d.get("name"), d.get("detection"), active, verbose) for d in detections]

    results["success"] = sorted(results["success"], 
            key=lambda i: i["original_name"] if i.get("original_name") else "")

    return results

@update.command()
@click.option("-v", "--verbose", count=True, help="Verbose output")
@click.option("-k", "--api-key", help="Key to include in API requests")
@click.option("-i", "--id", "message_data_model_id",
        help="Message data model ID to update", required=True
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
    help="Whether the message is safe or not"
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
        click.echo("Threat status is required")
        context.exit(-1)

    results = [api_client.review_message(
        message_data_model_id=message_data_model_id,
        reviewed=reviewed,
        safe=safe,
        verbose=verbose)]

    return results
