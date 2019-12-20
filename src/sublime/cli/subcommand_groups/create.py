"""CLI create subcommands."""

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
def create():
    """Create an item in your Sublime environment."""
    pass

@create.command()
@click.option("-v", "--verbose", count=True, help="Verbose output")
@click.option("-k", "--api-key", help="Key to include in API requests")
@click.option(
    "-D", "--detections", "detections_path", 
    type=click.Path(exists=True), 
    help="Detections file or directory [default: ./detections.pql]"
)
@click.option(
    "-d", "--detection", "detection_str", type=str,
    help=(
        "Raw detection. Instead of using a detections file, "
        "specify a single detection to be run directly surrounded "
        "by single quotes"
    )
)
@click.option("-a", "--active", "active", is_flag=True, default=False,
        help="Whether the detection should be enabled for live flow")
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
    active,
    output_file,
    output_format,
    verbose,
):
    """Create a detection."""
    if not detections_path and not detection_str:
        try:
            detections_path = click.open_file("detections.pql", mode="r")
        except FileNotFoundError as e:
            raise MissingDetectionInput

    if detections_path:
        if os.path.isfile(detections_path):
            with open(detections_path) as f:
                detections = load_detections(context, f)

        elif os.path.isdir(detections_path):
            detections = load_detections_path(context, detections_path)
    else:
        detections = [create_detection(detection_str)]

    results = [api_client.create_detection(d, active) for d in detections]

    return results
