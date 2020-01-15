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
    help="Change detection name"
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

        for d in detections:
            '''
            if not d["name"]:
                click.echo("Detection name required when using a PQL path/file")
                context.exit(-1)
            '''

            try:
                results["success"].append(api_client.update_detection_by_name(
                    d, active, verbose))
            except Exception as e:
                results["fail"].append(e.args[1])

    else:
        if not detection_id:
            click.echo("Detection ID or PQL file(s) is required")
            context.exit(-1)

        # depending on what we're updating, either of these could be null
        detection_str = detection_str if detection_str else ""
        detection_name = detection_name if detection_name else ""

        detections = [create_detection(detection_str, detection_name)]

        results["success"] = [api_client.update_detection_by_id(
            detection_id, d, active, verbose) for d in detections]

    results["success"] = sorted(results["success"], 
            key=lambda i: i["original_name"] if i.get("original_name") else "")

    return results
