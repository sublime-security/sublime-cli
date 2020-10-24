"""CLI backtest subcommands."""

import os
import platform
import time

import click

from sublime.__version__ import __version__
from sublime.cli.decorator import (
    echo_result,
    handle_exceptions,
    pass_api_client,
    MissingDetectionInput
)
from sublime.cli.helper import *
from sublime.error import JobError


@click.group()
def backtest():
    """Backtest across historical messages in your Sublime environment."""
    pass

@backtest.command()
@click.option("-v", "--verbose", count=True, help="Verbose output")
@click.option("-k", "--api-key", help="Key to include in API requests")
@click.option(
    "-D", "--detections", "detections_path", 
    type=click.Path(exists=True), 
    help="Detections file or directory"
)
@click.option("-i", "--id", "detection_id", 
        help="Detection ID")
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
@click.option("--after", "after", 
    type=click.DateTime(formats=get_datetime_formats()),
    help=(
        "Only analyze messages after this date. "
        "Default: last 24 hours. Format: ISO 8601"
    )
)
@click.option("--before", "before",
    type=click.DateTime(formats=get_datetime_formats()),
    help="Only analyze messages before this date. Format: ISO 8601"
)
@click.option("-l", "--limit", "limit", type=int, help="Message limit"
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
    after,
    before,
    limit,
    output_file,
    output_format,
    verbose,
):
    """Backtest a detection(s)."""

    if not detections_path and not detection_str and not detection_id:
        raise MissingDetectionInput

    if detections_path:
        if os.path.isfile(detections_path):
            with open(detections_path, encoding='utf-8') as f:
                detections = load_detections(f)

        elif os.path.isdir(detections_path):
            detections = load_detections_path(detections_path)
    elif detection_id:
        detections = [create_simple_detection(detection_id=detection_id)]
    else:
        detections = [create_simple_detection(detection_str=detection_str)]

    job_response = api_client.backtest_detections(detections, after, before, limit)
    job_id = job_response["job_id"]
    print(f"Job with ID {job_id} submitted")

    # no idea why this is required, but the second api_client call fails w/o it 
    api_client.session.close()

    while True:
        job_status_response = api_client.get_job_status(job_id)
        job_status = job_status_response["status"]

        if job_status == "running":
            print("Tasks remaining: {}".format(
                job_status_response["tasks_remaining"]))

        elif job_status == "pending":
            print("Job pending")

        elif job_status == "completed":
            results = api_client.get_job_output(job_id)

            # return the original backtest_detections results
            results = results["results"]
            break

        elif job_status == "failed":
            results = api_client.get_job_output(job_id)
            raise JobError(results["message"])

        else:
            raise JobError("Unrecognized job status")

        time.sleep(5)

    return results
