"""CLI create subcommands."""

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
def create():
    """Create an item in your Sublime environment."""
    pass

@create.command()
@click.option("-v", "--verbose", count=True, help="Verbose output")
@click.option("-k", "--api-key", help="Key to include in API requests")
@click.option(
    "-D", "--detections", "detections_path", 
    type=click.Path(exists=True), 
    help="Detections file or directory"
)
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
        "Detection name"
    )
)
@click.option("-a", "--active", "active", default="false", show_default=True,
    type=click.Choice(['true', 'false'], case_sensitive=False),
    help="Whether the detection should be enabled for live flow"
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
    detection_str,
    detection_name,
    active,
    output_file,
    output_format,
    verbose,
):
    """Create a detection."""
    if active == 'true':
        active = True
    else:
        active = False

    if not detections_path and not detection_str:
        raise MissingDetectionInput

    if detections_path:
        if os.path.isfile(detections_path):
            with open(detections_path, encoding='utf-8') as f:
                detections = load_detections(f)

        elif os.path.isdir(detections_path):
            detections = load_detections_path(detections_path)
    else:
        detections = [create_simple_detection(
            detection_str=detection_str, detection_name=detection_name)]

    # detection names are required on the backend, but they're not required
    # to just run in the CLI. so here we ensure each detection has a name
    for detection in detections:
        if not detection["name"]:
            LOGGER.error("Detection names are required")
            context.exit(-1)

    results = {"success": [], "fail": []}
    for d in detections:
        try:
            results["success"].append(api_client.create_detection(d, active))
        except Exception as e:
            results["fail"].append(e)

    results["success"] = sorted(results["success"], 
            key=lambda i: i["name"] if i.get("name") else "")

    return results
